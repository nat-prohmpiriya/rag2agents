"""Workflow execution engine."""

import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.workflow import Workflow, WorkflowExecution
from app.providers.llm import ChatMessage, llm_client

logger = logging.getLogger(__name__)


# =============================================================================
# Base Node Executor
# =============================================================================


class BaseNodeExecutor(ABC):
    """Base class for node executors."""

    node_type: str = "base"

    @abstractmethod
    async def execute(
        self,
        node_config: dict,
        state: dict,
        db: AsyncSession,
    ) -> dict:
        """
        Execute the node.

        Args:
            node_config: Node configuration from the workflow
            state: Current workflow state
            db: Database session

        Returns:
            Node execution result
        """
        pass


# =============================================================================
# Node Executor Implementations
# =============================================================================


class StartNodeExecutor(BaseNodeExecutor):
    """Start node - workflow entry point."""

    node_type = "start"

    async def execute(self, node_config: dict, state: dict, db: AsyncSession) -> dict:
        """Pass through inputs."""
        return {"output": state.get("inputs", {})}


class EndNodeExecutor(BaseNodeExecutor):
    """End node - workflow exit point."""

    node_type = "end"

    async def execute(self, node_config: dict, state: dict, db: AsyncSession) -> dict:
        """Collect final outputs."""
        # Get output from previous node
        output_from = node_config.get("config", {}).get("output_from")
        if output_from and output_from in state.get("node_outputs", {}):
            return {"output": state["node_outputs"][output_from]}
        # Return last node output
        node_outputs = state.get("node_outputs", {})
        if node_outputs:
            last_key = list(node_outputs.keys())[-1]
            return {"output": node_outputs[last_key]}
        return {"output": None}


class LLMNodeExecutor(BaseNodeExecutor):
    """LLM node - call LiteLLM for text generation."""

    node_type = "llm"

    async def execute(self, node_config: dict, state: dict, db: AsyncSession) -> dict:
        """Execute LLM call."""
        config = node_config.get("config", {})

        # Get prompt template and render with state
        prompt_template = config.get("prompt", "")
        prompt = self._render_template(prompt_template, state)

        # Get model settings
        model = config.get("model", "gemini-2.0-flash")
        temperature = config.get("temperature", 0.7)
        max_tokens = config.get("max_tokens")
        system_prompt = config.get("system_prompt")

        # Build messages
        messages = []
        if system_prompt:
            messages.append(ChatMessage(role="system", content=system_prompt))
        messages.append(ChatMessage(role="user", content=prompt))

        # Call LLM
        response = await llm_client.chat_completion(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        return {
            "output": response.content,
            "tokens_used": response.usage.get("total_tokens", 0) if response.usage else 0,
        }

    def _render_template(self, template: str, state: dict) -> str:
        """Render template with state variables."""
        result = template
        # Replace {{variable}} patterns
        node_outputs = state.get("node_outputs", {})
        inputs = state.get("inputs", {})

        # Replace input variables
        for key, value in inputs.items():
            result = result.replace(f"{{{{{key}}}}}", str(value))

        # Replace node output variables
        for node_id, output in node_outputs.items():
            if isinstance(output, dict) and "output" in output:
                result = result.replace(f"{{{{nodes.{node_id}}}}}", str(output["output"]))
            else:
                result = result.replace(f"{{{{nodes.{node_id}}}}}", str(output))

        return result


class RAGNodeExecutor(BaseNodeExecutor):
    """RAG node - search documents."""

    node_type = "rag"

    async def execute(self, node_config: dict, state: dict, db: AsyncSession) -> dict:
        """Execute RAG search."""
        from app.services.rag import rag_service

        config = node_config.get("config", {})

        # Get query
        query_from = config.get("query_from", "inputs.query")
        query = self._get_value_from_path(query_from, state)
        if not query:
            query = config.get("query", "")

        # Get search params
        top_k = config.get("top_k", 5)
        document_ids = config.get("document_ids", [])

        # Execute search
        results = await rag_service.search(
            db=db,
            query=query,
            top_k=top_k,
            document_ids=document_ids if document_ids else None,
        )

        # Format results
        context_parts = []
        sources = []
        for chunk in results:
            context_parts.append(chunk.content)
            sources.append({
                "document_id": str(chunk.document_id),
                "chunk_index": chunk.chunk_index,
                "score": chunk.score if hasattr(chunk, "score") else None,
            })

        return {
            "output": "\n\n".join(context_parts),
            "sources": sources,
            "chunk_count": len(results),
        }

    def _get_value_from_path(self, path: str, state: dict) -> Any:
        """Get value from dot-notation path."""
        parts = path.split(".")
        current = state
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None
        return current


class AgentNodeExecutor(BaseNodeExecutor):
    """Agent node - use existing agent system."""

    node_type = "agent"

    async def execute(self, node_config: dict, state: dict, db: AsyncSession) -> dict:
        """Execute agent."""
        from app.agents.engine import AgentEngine

        config = node_config.get("config", {})

        # Get agent slug
        agent_slug = config.get("agent_slug", "general")

        # Get input
        input_from = config.get("input_from", "inputs.query")
        user_input = self._get_value_from_path(input_from, state)
        if not user_input:
            user_input = config.get("input", "")

        # Get context from previous nodes if specified
        context_from = config.get("context_from")
        context = None
        if context_from:
            context = self._get_value_from_path(context_from, state)

        # Build messages
        messages = []
        if context:
            messages.append({
                "role": "system",
                "content": f"Context:\n{context}",
            })
        messages.append({
            "role": "user",
            "content": user_input,
        })

        # Execute agent
        engine = AgentEngine(db, agent_slug)
        result = await engine.run(messages)

        return {
            "output": result.get("response", ""),
            "tool_calls": result.get("tool_calls", []),
            "tokens_used": result.get("tokens_used", 0),
        }

    def _get_value_from_path(self, path: str, state: dict) -> Any:
        """Get value from dot-notation path."""
        parts = path.split(".")
        current = state
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None
        return current


class ConditionNodeExecutor(BaseNodeExecutor):
    """Condition node - if/else branching."""

    node_type = "condition"

    async def execute(self, node_config: dict, state: dict, db: AsyncSession) -> dict:
        """Evaluate condition."""
        config = node_config.get("config", {})

        # Get value to check
        variable = config.get("variable", "")
        value = self._get_value_from_path(variable, state)

        # Get operator and compare value
        operator = config.get("operator", "equals")
        compare_value = config.get("value", "")

        # Evaluate condition
        result = self._evaluate(value, operator, compare_value)

        return {
            "output": result,
            "branch": "true" if result else "false",
        }

    def _get_value_from_path(self, path: str, state: dict) -> Any:
        """Get value from dot-notation path."""
        parts = path.split(".")
        current = state
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None
        return current

    def _evaluate(self, value: Any, operator: str, compare_value: Any) -> bool:
        """Evaluate condition."""
        if operator == "equals":
            return str(value) == str(compare_value)
        elif operator == "not_equals":
            return str(value) != str(compare_value)
        elif operator == "contains":
            return str(compare_value) in str(value)
        elif operator == "not_contains":
            return str(compare_value) not in str(value)
        elif operator == "greater_than":
            try:
                return float(value) > float(compare_value)
            except (ValueError, TypeError):
                return False
        elif operator == "less_than":
            try:
                return float(value) < float(compare_value)
            except (ValueError, TypeError):
                return False
        elif operator == "is_empty":
            return not value
        elif operator == "is_not_empty":
            return bool(value)
        return False


class LoopNodeExecutor(BaseNodeExecutor):
    """Loop node - iterate over items."""

    node_type = "loop"

    async def execute(self, node_config: dict, state: dict, db: AsyncSession) -> dict:
        """Execute loop iteration."""
        config = node_config.get("config", {})

        # Get array to iterate
        array_from = config.get("array_from", "")
        array = self._get_value_from_path(array_from, state)

        if not isinstance(array, list):
            return {"output": [], "items": [], "count": 0}

        # Get current iteration index
        loop_state = state.get("loop_state", {})
        node_id = node_config.get("id", "")
        current_index = loop_state.get(f"{node_id}_index", 0)

        if current_index >= len(array):
            return {
                "output": loop_state.get(f"{node_id}_results", []),
                "done": True,
                "count": len(array),
            }

        return {
            "output": array[current_index],
            "index": current_index,
            "done": False,
            "count": len(array),
        }

    def _get_value_from_path(self, path: str, state: dict) -> Any:
        """Get value from dot-notation path."""
        parts = path.split(".")
        current = state
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None
        return current


class HTTPNodeExecutor(BaseNodeExecutor):
    """HTTP node - call external APIs."""

    node_type = "http"

    async def execute(self, node_config: dict, state: dict, db: AsyncSession) -> dict:
        """Execute HTTP request."""
        import httpx

        config = node_config.get("config", {})

        method = config.get("method", "GET").upper()
        url = self._render_template(config.get("url", ""), state)
        headers = config.get("headers", {})
        body = config.get("body")

        if body:
            body = self._render_template(str(body), state)

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                if method == "GET":
                    response = await client.get(url, headers=headers)
                elif method == "POST":
                    response = await client.post(url, headers=headers, json=body if body else None)
                elif method == "PUT":
                    response = await client.put(url, headers=headers, json=body if body else None)
                elif method == "DELETE":
                    response = await client.delete(url, headers=headers)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")

                return {
                    "output": response.text,
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                }
        except Exception as e:
            return {
                "output": None,
                "error": str(e),
                "status_code": 0,
            }

    def _render_template(self, template: str, state: dict) -> str:
        """Render template with state variables."""
        result = template
        node_outputs = state.get("node_outputs", {})
        inputs = state.get("inputs", {})

        for key, value in inputs.items():
            result = result.replace(f"{{{{{key}}}}}", str(value))

        for node_id, output in node_outputs.items():
            if isinstance(output, dict) and "output" in output:
                result = result.replace(f"{{{{nodes.{node_id}}}}}", str(output["output"]))

        return result


class CustomFunctionNodeExecutor(BaseNodeExecutor):
    """Custom function node - run custom Python code."""

    node_type = "custom_function"

    async def execute(self, node_config: dict, state: dict, db: AsyncSession) -> dict:
        """Execute custom Python code (sandboxed)."""
        config = node_config.get("config", {})
        code = config.get("code", "")

        # Prepare execution context
        inputs = state.get("inputs", {})
        node_outputs = state.get("node_outputs", {})

        # Build safe globals
        safe_globals = {
            "inputs": inputs,
            "nodes": node_outputs,
            "result": None,
        }

        # Execute code
        try:
            exec(code, safe_globals)
            return {"output": safe_globals.get("result")}
        except Exception as e:
            return {"output": None, "error": str(e)}


# =============================================================================
# Node Executor Registry
# =============================================================================


NODE_EXECUTORS: dict[str, type[BaseNodeExecutor]] = {
    "start": StartNodeExecutor,
    "end": EndNodeExecutor,
    "llm": LLMNodeExecutor,
    "rag": RAGNodeExecutor,
    "agent": AgentNodeExecutor,
    "condition": ConditionNodeExecutor,
    "loop": LoopNodeExecutor,
    "http": HTTPNodeExecutor,
    "custom_function": CustomFunctionNodeExecutor,
}


# =============================================================================
# Workflow Engine
# =============================================================================


class WorkflowEngine:
    """Workflow execution engine."""

    def __init__(
        self,
        workflow: Workflow,
        execution: WorkflowExecution,
        db: AsyncSession,
    ):
        self.workflow = workflow
        self.execution = execution
        self.db = db
        self.state: dict[str, Any] = {
            "inputs": {},
            "node_outputs": {},
            "loop_state": {},
        }
        self.logs: list[dict] = []
        self.total_tokens: int = 0

    async def execute(self, inputs: dict) -> dict:
        """
        Execute the workflow.

        Args:
            inputs: Workflow inputs

        Returns:
            Execution result with outputs, node_states, and logs
        """
        self.state["inputs"] = inputs
        nodes = self.workflow.nodes or []
        edges = self.workflow.edges or []

        if not nodes:
            return {
                "outputs": {},
                "node_states": {},
                "logs": [],
                "total_tokens": 0,
            }

        # Build adjacency map for traversal
        adjacency = self._build_adjacency(edges)

        # Find start node
        start_node = self._find_start_node(nodes)
        if not start_node:
            raise ValueError("No start node found in workflow")

        # Execute nodes in order
        current_node = start_node
        visited = set()

        while current_node:
            node_id = current_node.get("id")
            if node_id in visited:
                # Prevent infinite loops (except for loop nodes)
                node_type = current_node.get("data", {}).get("type", "")
                if node_type != "loop":
                    break

            visited.add(node_id)

            # Execute node
            result = await self._execute_node(current_node)
            self.state["node_outputs"][node_id] = result

            # Get next node
            node_type = current_node.get("data", {}).get("type", "")

            if node_type == "end":
                # End node - finish execution
                break
            elif node_type == "condition":
                # Condition node - branch based on result
                branch = result.get("branch", "true")
                next_node = self._get_next_node_for_branch(node_id, branch, edges, nodes)
            else:
                # Normal node - follow edges
                next_node = self._get_next_node(node_id, adjacency, nodes)

            current_node = next_node

        # Return final outputs
        return {
            "outputs": self.state["node_outputs"],
            "node_states": self.state["node_outputs"],
            "logs": self.logs,
            "total_tokens": self.total_tokens,
        }

    async def _execute_node(self, node: dict) -> dict:
        """Execute a single node."""
        node_id = node.get("id", "")
        node_data = node.get("data", {})
        node_type = node_data.get("type", "")
        node_config = node_data.get("config", {})

        # Get executor
        executor_class = NODE_EXECUTORS.get(node_type)
        if not executor_class:
            logger.warning(f"Unknown node type: {node_type}")
            return {"output": None, "error": f"Unknown node type: {node_type}"}

        executor = executor_class()

        # Log start
        log_entry = {
            "node_id": node_id,
            "node_type": node_type,
            "status": "running",
            "started_at": datetime.now(timezone.utc).isoformat(),
        }

        try:
            # Execute
            result = await executor.execute(
                {"id": node_id, "config": node_config},
                self.state,
                self.db,
            )

            # Update tokens
            tokens_used = result.get("tokens_used", 0)
            self.total_tokens += tokens_used

            # Log completion
            log_entry["status"] = "completed"
            log_entry["completed_at"] = datetime.now(timezone.utc).isoformat()
            log_entry["output"] = result
            log_entry["tokens_used"] = tokens_used

            self.logs.append(log_entry)
            return result

        except Exception as e:
            logger.error(f"Node {node_id} execution failed: {e}")
            log_entry["status"] = "failed"
            log_entry["completed_at"] = datetime.now(timezone.utc).isoformat()
            log_entry["error"] = str(e)
            self.logs.append(log_entry)
            return {"output": None, "error": str(e)}

    def _build_adjacency(self, edges: list) -> dict[str, list[str]]:
        """Build adjacency map from edges."""
        adjacency: dict[str, list[str]] = {}
        for edge in edges:
            source = edge.get("source", "")
            target = edge.get("target", "")
            if source not in adjacency:
                adjacency[source] = []
            adjacency[source].append(target)
        return adjacency

    def _find_start_node(self, nodes: list) -> dict | None:
        """Find the start node."""
        for node in nodes:
            node_type = node.get("data", {}).get("type", "")
            if node_type == "start":
                return node
        return nodes[0] if nodes else None

    def _get_next_node(
        self,
        current_id: str,
        adjacency: dict[str, list[str]],
        nodes: list,
    ) -> dict | None:
        """Get the next node to execute."""
        targets = adjacency.get(current_id, [])
        if not targets:
            return None

        target_id = targets[0]  # Take first target for non-branching nodes
        for node in nodes:
            if node.get("id") == target_id:
                return node
        return None

    def _get_next_node_for_branch(
        self,
        source_id: str,
        branch: str,
        edges: list,
        nodes: list,
    ) -> dict | None:
        """Get next node for condition branch."""
        for edge in edges:
            if edge.get("source") == source_id:
                # Check if edge has label matching branch
                edge_label = edge.get("label", "").lower()
                source_handle = edge.get("sourceHandle", "").lower()

                if branch == "true" and (edge_label == "true" or source_handle == "true" or not edge_label):
                    target_id = edge.get("target")
                    for node in nodes:
                        if node.get("id") == target_id:
                            return node
                elif branch == "false" and (edge_label == "false" or source_handle == "false"):
                    target_id = edge.get("target")
                    for node in nodes:
                        if node.get("id") == target_id:
                            return node

        return None

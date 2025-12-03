# Phase 4: Agent System - Implementation Prompts

## Overview

**Goal**: User can select agents (General, HR, Legal, Finance, Research, Mental Health) for different tasks.

**Architecture**:
```
User Query → Agent Router → Selected Agent → Tools → Response
```

**Pre-built Agents** (6 ตัว):
| Slug | Name | Icon | Tools |
|------|------|------|-------|
| general | General Assistant | 🤖 | rag_search, summarize |
| hr | HR Assistant | 👥 | rag_search, summarize |
| legal | Legal Assistant | ⚖️ | rag_search, summarize |
| finance | Finance Assistant | 💰 | rag_search, summarize, calculator |
| research | Research Assistant | 🔬 | rag_search, summarize |
| mental_health | Mental Health Research | 🧠 | rag_search, summarize (PII-strict) |

---

## Backend Tasks

### Task B1: Agent Models & Schemas

**Files**: `backend/app/models/agent.py`, `backend/app/schemas/agent.py`

**Context** (อ่านก่อน):
- `backend/app/models/user.py` - ดู model pattern
- `backend/app/schemas/chat.py` - ดู schema pattern

**Requirements**:
1. Create `Agent` model with fields: id, user_id (nullable), name, slug (unique), description, icon, system_prompt, tools (JSON), config (JSON), is_active, timestamps
2. Create schemas: `AgentInfo`, `AgentCreate`, `AgentUpdate`, `ToolInfo`, `AgentListResponse`
3. Create `AgentTool` enum: rag_search, summarize, calculator, web_search
4. Export in `__init__.py`

**Testing**:
```bash
cd backend && uv run python -c "from app.models.agent import Agent; print('OK')"
cd backend && uv run python -c "from app.schemas.agent import AgentInfo; print('OK')"
```

---

### Task B2: Agent Config Loader (YAML)

**Files**: `backend/configs/agents/*.yaml`, `backend/app/services/agent_loader.py`

**Context**:
- `.docs/02-spec.md` section 4.2 - Mental Health Agent spec

**Requirements**:
1. Create 6 YAML files in `configs/agents/`: general.yaml, hr.yaml, legal.yaml, finance.yaml, research.yaml, mental_health.yaml
2. YAML structure: agent (name, slug, icon, description), persona (system_prompt), tools (list), settings (temperature, max_tokens), privacy (for mental_health only)
3. Create `AgentLoader` class with methods: `load_agent(slug)`, `list_agents()`, `get_system_prompt(slug)`
4. Use `@lru_cache` for caching
5. Export singleton `agent_loader`

**Testing**:
```bash
cd backend && uv run python -c "
from app.services.agent_loader import agent_loader
print(f'Found {len(agent_loader.list_agents())} agents')
"
```

---

### Task B3: Agent Tools

**Files**: `backend/app/agents/tools/` directory

**Context**:
- `backend/app/services/rag.py` - ใช้สำหรับ RAG tool
- `backend/app/providers/llm.py` - ใช้สำหรับ Summarize tool

**Requirements**:
1. Create `base.py`: `BaseTool` (ABC) with `execute()`, `ToolResult` schema
2. Create `rag_search.py`: Use existing `rag_service.retrieve_context()`
3. Create `summarize.py`: Use `llm_client` to summarize text
4. Create `calculator.py`: Safe math eval using `ast.literal_eval` (NO eval/exec!)
5. Create `__init__.py`: `TOOL_REGISTRY` dict and `get_tool(name)` function

**Testing**:
```bash
cd backend && uv run python -c "
from app.agents.tools import TOOL_REGISTRY
print(f'Tools: {list(TOOL_REGISTRY.keys())}')
"
```

---

### Task B4: Agent Engine

**Files**: `backend/app/agents/engine.py`

**Context**:
- `backend/app/routes/chat.py` - ดู chat flow
- Task B2 output - agent_loader
- Task B3 output - tools

**Requirements**:
1. Create `AgentEngine` class with: `__init__(agent_slug)`, `process()`, `process_stream()`
2. Build system prompt with agent persona + tools description
3. Simple tool calling: Parse `<tool>{"name": "...", "params": {...}}</tool>` from LLM response
4. Execute tools sequentially, feed results back to LLM
5. Create `AgentResponse` schema: content, tools_used, thinking, sources

**Key Notes**:
- ไม่ใช้ LangChain - ทำ simple tool calling เอง
- Streaming: show thinking → tool calls → final response

**Testing**:
```bash
cd backend && uv run python -c "
from app.agents.engine import AgentEngine
engine = AgentEngine('general')
print(f'Tools: {list(engine.tools.keys())}')
"
```

---

### Task B5: Agent Routes

**Files**: `backend/app/routes/agents.py`, update `routes/chat.py`

**Context**:
- `backend/app/routes/projects.py` - ดู route pattern
- Task B4 output - AgentEngine

**Requirements**:
1. Create routes: `GET /agents`, `GET /agents/{slug}`, `GET /agents/{slug}/tools`
2. Update `ChatRequest` schema: add `agent_slug: str | None`
3. Update chat endpoints: if `agent_slug` provided, use `AgentEngine` instead of direct LLM call
4. Register in `main.py`

**API Endpoints**:
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/agents | List all agents |
| GET | /api/agents/{slug} | Get agent details |
| POST | /api/chat | Chat with agent (agent_slug param) |

**Testing**:
```bash
TOKEN="your-jwt-token"
curl -s http://localhost:8000/api/agents -H "Authorization: Bearer $TOKEN" | jq
curl -s -X POST http://localhost:8000/api/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "What is 25*4?", "agent_slug": "finance"}' | jq
```

---

## Frontend Tasks

### Task F1: Agent API Client

**Files**: `frontend/src/lib/api/agents.ts`

**Context**:
- `frontend/src/lib/api/chat.ts` - ดู pattern
- `frontend/src/lib/api/client.ts` - ดู apiClient

**Requirements**:
1. Create types: `AgentInfo`, `ToolInfo`, `AgentListResponse`
2. Create functions: `listAgents()`, `getAgent(slug)`, `getAgentTools(slug)`
3. Update `ChatRequest` in chat.ts: add `agent_slug?: string`
4. Export in `index.ts`

**Testing**: `cd frontend && npm run check`

---

### Task F2: Agent Store

**Files**: `frontend/src/lib/stores/agents.svelte.ts`

**Context**:
- `frontend/src/lib/stores/sidebar.svelte.ts` - ดู Svelte 5 store pattern

**Requirements**:
1. State: `agents`, `selectedAgentSlug`, `isLoading`, `error` (use `$state()`)
2. Derived: `selectedAgent` (use `$derived()`)
3. Actions: `fetchAgents()`, `selectAgent(slug)`, `initFromStorage()`
4. Persist selection to localStorage
5. Export as `agentStore` with getters

**Testing**: `cd frontend && npm run check`

---

### Task F3: Agent Selector Component

**Files**: `frontend/src/lib/components/agents/AgentSelector.svelte`

**Context**:
- `frontend/src/lib/components/llm-chat/ModelSelector.svelte` - ดู pattern
- `frontend/src/lib/components/ui/select/` - ดู Select component

**Requirements**:
1. Dropdown with agent icon + name
2. "No Agent (Direct Chat)" option
3. Load agents on mount, persist selection
4. Props: `onSelect?: (slug: string | null) => void`

**Testing**: `cd frontend && npm run check && npm run build`

---

### Task F4: Agent Card Component

**Files**: `frontend/src/lib/components/agents/AgentCard.svelte`

**Context**:
- `frontend/src/lib/components/ui/card/` - ดู Card
- `frontend/src/lib/components/ui/badge/` - ดู Badge

**Requirements**:
1. Show: icon, name, description, tools (as badges)
2. Props: `agent: AgentInfo`, `selected?: boolean`, `onclick?: () => void`
3. Highlight when selected

**Testing**: `cd frontend && npm run check`

---

### Task F5: Agent Thinking Component

**Files**: `frontend/src/lib/components/agents/AgentThinking.svelte`

**Context**:
- `frontend/src/lib/components/llm-chat/LLMChat.svelte` - ดู streaming pattern

**Requirements**:
1. Display step-by-step: thinking, tool_call, tool_result
2. Show tool icons and status (running/done/error)
3. Props: `steps: Array<{type, content, toolName?, status?}>`

**Testing**: `cd frontend && npm run check`

---

### Task F6: Chat Integration

**Files**: Update `LLMChat.svelte`, `ChatHeader.svelte`

**Context**:
- Task F2 output - agentStore
- Task F3 output - AgentSelector

**Requirements**:
1. Add AgentSelector to ChatHeader
2. Pass `agent_slug` in chat requests from agentStore
3. Show selected agent info in chat

**Testing**: Manual - select agent, send message, verify agent_slug in request

---

### Task F7: Agents Page

**Files**: `frontend/src/routes/(app)/agents/+page.svelte`

**Context**:
- `frontend/src/routes/(app)/documents/+page.svelte` - ดู page pattern

**Requirements**:
1. Grid of AgentCard components
2. Click agent → select + redirect to /chat
3. Add "Agents" link to Sidebar

**Testing**: Navigate to /agents, click agent, verify redirect

---

## Execution Order

```
Backend:  B1 → B2 → B3 → B4 → B5
Frontend: F1 → F2 → F3 → F4 → F5 → F6 → F7
```

---

## API Testing (After All Backend Done)

```bash
# 1. Get token
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}' | jq -r '.data.access_token')

# 2. List agents
curl -s http://localhost:8000/api/agents \
  -H "Authorization: Bearer $TOKEN" | jq

# 3. Get specific agent
curl -s http://localhost:8000/api/agents/finance \
  -H "Authorization: Bearer $TOKEN" | jq

# 4. Chat with agent (calculator)
curl -s -X POST http://localhost:8000/api/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "What is 25 * 4?", "agent_slug": "finance"}' | jq

# 5. Chat with agent (RAG)
curl -s -X POST http://localhost:8000/api/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "What are the benefits?", "agent_slug": "hr", "use_rag": true}' | jq
```

---

## Quick Reference

### Svelte 5 Runes
```svelte
let count = $state(0);
let doubled = $derived(count * 2);
let { name }: { name: string } = $props();
```

### Python Type Hints
```python
async def get_agent(slug: str) -> Agent | None:
```

### BaseResponse Pattern
```python
return BaseResponse(trace_id=ctx.trace_id, data=AgentInfo.model_validate(agent))
```

---

*Last updated: December 2024*

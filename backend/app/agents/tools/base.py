"""Base tool interface for agent tools."""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ToolResult:
    """Result from tool execution."""

    success: bool
    data: Any = None
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "metadata": self.metadata,
        }


class BaseTool(ABC):
    """Abstract base class for agent tools."""

    name: str = "base_tool"
    description: str = "Base tool"

    @abstractmethod
    async def execute(self, **kwargs: Any) -> ToolResult:
        """Execute the tool with given parameters.

        Args:
            **kwargs: Tool-specific parameters

        Returns:
            ToolResult with success status and data/error
        """
        pass

    def get_schema(self) -> dict[str, Any]:
        """Get tool schema for function calling.

        Returns:
            OpenAI-compatible function schema
        """
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self._get_parameters_schema(),
            },
        }

    def _get_parameters_schema(self) -> dict[str, Any]:
        """Get parameters JSON schema. Override in subclasses.

        Returns:
            JSON Schema for tool parameters
        """
        return {
            "type": "object",
            "properties": {},
            "required": [],
        }

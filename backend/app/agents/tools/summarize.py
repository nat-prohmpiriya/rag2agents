"""Summarize tool for condensing text content."""

import logging
from typing import Any

from app.agents.tools.base import BaseTool, ToolResult
from app.providers.llm import ChatMessage, llm_client

logger = logging.getLogger(__name__)


class SummarizeTool(BaseTool):
    """Tool for summarizing text content using LLM."""

    name = "summarize"
    description = "Summarize long text content into a concise summary"

    async def execute(
        self,
        text: str,
        max_length: int = 500,
        style: str = "concise",
        **kwargs: Any,
    ) -> ToolResult:
        """Execute summarization.

        Args:
            text: Text content to summarize
            max_length: Approximate max length of summary in words
            style: Summary style - 'concise', 'detailed', or 'bullet_points'

        Returns:
            ToolResult with summary text
        """
        if not text or not text.strip():
            return ToolResult(
                success=False,
                error="No text provided for summarization",
            )

        try:
            # Build prompt based on style
            style_instructions = {
                "concise": "Provide a brief, concise summary.",
                "detailed": "Provide a comprehensive summary covering all key points.",
                "bullet_points": "Provide a summary as bullet points.",
            }

            instruction = style_instructions.get(style, style_instructions["concise"])

            messages = [
                ChatMessage(
                    role="system",
                    content=f"""You are a summarization assistant. {instruction}
Keep the summary under approximately {max_length} words.
Focus on the most important information and key takeaways.""",
                ),
                ChatMessage(
                    role="user",
                    content=f"Please summarize the following text:\n\n{text}",
                ),
            ]

            response = await llm_client.chat_completion(
                messages=messages,
                temperature=0.3,  # Lower temperature for consistent summaries
                max_tokens=max_length * 2,  # Rough estimate for tokens
            )

            return ToolResult(
                success=True,
                data=response.content,
                metadata={
                    "style": style,
                    "max_length": max_length,
                    "model": response.model,
                    "usage": response.usage,
                },
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=str(e),
            )

    def _get_parameters_schema(self) -> dict[str, Any]:
        """Get parameters schema for summarize tool."""
        return {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "The text content to summarize",
                },
                "max_length": {
                    "type": "integer",
                    "description": "Approximate max length of summary in words (default: 500)",
                    "default": 500,
                },
                "style": {
                    "type": "string",
                    "enum": ["concise", "detailed", "bullet_points"],
                    "description": "Summary style (default: concise)",
                    "default": "concise",
                },
            },
            "required": ["text"],
        }


# Singleton instance
summarize_tool = SummarizeTool()

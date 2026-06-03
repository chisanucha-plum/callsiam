"""ConversationMessage dataclass."""

from dataclasses import dataclass


@dataclass
class ConversationMessage:
    """Message in conversation history."""

    role: str  # "system", "user", "assistant"
    content: str

    def to_dict(self) -> dict:
        """Convert to dictionary for LLM API."""
        return {"role": self.role, "content": self.content}

    @staticmethod
    def system(content: str) -> "ConversationMessage":
        """Create system message."""
        return ConversationMessage(role="system", content=content)

    @staticmethod
    def user(content: str) -> "ConversationMessage":
        """Create user message."""
        return ConversationMessage(role="user", content=content)

    @staticmethod
    def assistant(content: str) -> "ConversationMessage":
        """Create assistant message."""
        return ConversationMessage(role="assistant", content=content)

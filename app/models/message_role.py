"""MessageRole enumeration."""

from enum import Enum


class MessageRole(str, Enum):
    """Message roles for conversation."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"

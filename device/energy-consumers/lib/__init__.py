"""Shared types and registry loading for energy consumer monitoring."""

from .consumer_schema import ConsumerStatus, validate_status_payload
from .registry import load_consumers_registry

__all__ = [
    "ConsumerStatus",
    "validate_status_payload",
    "load_consumers_registry",
]

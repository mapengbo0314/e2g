"""Work-unit definitions for indexing tasks."""

from dataclasses import dataclass


@dataclass(slots=True)
class WorkUnit:
    unit_id: str
    description: str = ""
    status: str = "pending"

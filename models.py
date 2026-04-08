from typing import Optional, Dict, Any, List, Literal
from openenv.core.env_server.types import Action, Observation
from pydantic import Field


class EmailAction(Action):
    action_type: Literal[
        "list_emails",
        "read_email",
        "classify_email",
        "reply_email",
        "archive_email"
    ]

    email_id: Optional[str] = None
    category: Optional[str] = None
    reply_content: Optional[str] = None


class EmailObservation(Observation):
    success: bool = True
    error_message: Optional[str] = None

    emails: Optional[List[Dict[str, Any]]] = None
    current_email: Optional[Dict[str, Any]] = None

    message: Optional[str] = None

    done: bool = False
    reward: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
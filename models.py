from typing import Optional, Dict, Any, List, Literal  
# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

from datetime import datetime, timedelta  
from openenv.core.env_server.types import Action, Observation  
from pydantic import BaseModel, Field  
  
  
class EmailAction(Action):  
    action_type: Literal[  
        "list_emails",  
        "read_email",   
        "classify_email",  
        "reply_email",  
        "archive_email",  
        "draft_email",  
        "organize_emails",  
        "auto_respond",  
        "get_thread_insights",  
        "schedule_followup",  
        "send_scheduled_emails"  
    ]  
  
    # Existing fields  
    email_id: Optional[str] = None  
    category: Optional[str] = None  
    reply_content: Optional[str] = None  
  
    # New fields for advanced features  
    draft_content: Optional[str] = None  
    draft_recipient: Optional[str] = None  
    draft_subject: Optional[str] = None  
    tone: Optional[str] = None  
      
    organize_criteria: Optional[Dict[str, Any]] = None  
    priority_filter: Optional[str] = None  
      
    auto_response_rules: Optional[Dict[str, Any]] = None  
      
    thread_id: Optional[str] = None  
      
    followup_email_id: Optional[str] = None  
    followup_delay: Optional[int] = None  
    followup_message: Optional[str] = None  
  
  
class EmailObservation(Observation):  
    # Existing fields  
    success: bool = True  
    error_message: Optional[str] = None  
    emails: Optional[List[Dict[str, Any]]] = None  
    current_email: Optional[Dict[str, Any]] = None  
    message: Optional[str] = None  
    metadata: Dict[str, Any] = Field(default_factory=dict)  
  
    # New fields for advanced features  
    draft_email: Optional[Dict[str, Any]] = None  
    organized_emails: Optional[Dict[str, List[Dict[str, Any]]]] = None  
    auto_responses: Optional[List[Dict[str, Any]]] = None  
    thread_insights: Optional[Dict[str, Any]] = None  
    scheduled_followups: Optional[List[Dict[str, Any]]] = None  
    sent_emails: Optional[List[Dict[str, Any]]] = None  
  
  
class EmailState(BaseModel):  
    episode_id: str  
    step_count: int = 0  
    task_name: str = ""  
    drafts: List[Dict[str, Any]] = Field(default_factory=list)  
    scheduled_emails: List[Dict[str, Any]] = Field(default_factory=list)  
    auto_response_rules: Dict[str, Any] = Field(default_factory=dict)  
    thread_summaries: Dict[str, str] = Field(default_factory=dict)  
    actions_history: List[Dict[str, Any]] = Field(default_factory=list)
# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""Email Env Environment Client."""  

  
from typing import Dict, List, Optional, Any  
  
from openenv.core import EnvClient  
from openenv.core.client_types import StepResult  
from openenv.core.env_server.types import State  
  
from .models import EmailAction, EmailObservation, EmailState
  
  
class EmailEnv(EnvClient[EmailAction, EmailObservation, State]):  
    """Client for email environment with advanced features."""  
  
    def _step_payload(self, action: EmailAction) -> Dict:  
        """Convert action to JSON payload."""  
        payload = {  
            "action_type": action.action_type,  
            "email_id": action.email_id,  
            "category": action.category,  
            "reply_content": action.reply_content,  
        }  
          
        # Add new fields for advanced actions  
        if hasattr(action, 'draft_content'):  
            payload.update({  
                "draft_content": action.draft_content,  
                "draft_recipient": action.draft_recipient,  
                "draft_subject": action.draft_subject,  
                "tone": action.tone,  
            })  
          
        if hasattr(action, 'organize_criteria'):  
            payload.update({  
                "organize_criteria": action.organize_criteria,  
                "priority_filter": action.priority_filter,  
            })  
              
        if hasattr(action, 'auto_response_rules'):  
            payload["auto_response_rules"] = action.auto_response_rules  
              
        if hasattr(action, 'thread_id'):  
            payload["thread_id"] = action.thread_id  
              
        if hasattr(action, 'followup_email_id'):  
            payload.update({  
                "followup_email_id": action.followup_email_id,  
                "followup_delay": action.followup_delay,  
                "followup_message": action.followup_message,  
            })  
          
        return payload  
  
    def _parse_result(self, payload: Dict) -> StepResult[EmailObservation]:  
        """Parse server response."""  
        obs_data = payload.get("observation", {})  
  
        observation = EmailObservation(  
            success=obs_data.get("success", True),  
            error_message=obs_data.get("error_message"),  
            emails=obs_data.get("emails"),  
            current_email=obs_data.get("current_email"),  
            message=obs_data.get("message"),  
            metadata=obs_data.get("metadata", {}),  
            done=obs_data.get("done", False),  
            reward=payload.get("reward", 0.0),  
            # New fields for advanced features  
            draft_email=obs_data.get("draft_email"),  
            organized_emails=obs_data.get("organized_emails"),  
            auto_responses=obs_data.get("auto_responses"),  
            thread_insights=obs_data.get("thread_insights"),  
            scheduled_followups=obs_data.get("scheduled_followups"),  
            sent_emails=obs_data.get("sent_emails"),  
        )  
  
        return StepResult(  
            observation=observation,  
            reward=payload.get("reward"),  
            done=payload.get("done", False),  
        )  
  
    def _parse_state(self, payload: Dict) -> State:  
        """Parse state response."""  
        return State(  
            episode_id=payload.get("episode_id"),  
            step_count=payload.get("step_count", 0),  
        )  
  
    # Convenience methods for common actions  
    async def list_emails(self) -> StepResult[EmailObservation]:  
        """List all emails."""  
        return await self.step(EmailAction(action_type="list_emails"))  
  
    async def read_email(self, email_id: str) -> StepResult[EmailObservation]:  
        """Read a specific email."""  
        return await self.step(EmailAction(  
            action_type="read_email",  
            email_id=email_id  
        ))  
  
    async def classify_email(self, email_id: str, category: str) -> StepResult[EmailObservation]:  
        """Classify an email."""  
        return await self.step(EmailAction(  
            action_type="classify_email",  
            email_id=email_id,  
            category=category  
        ))  
  
    async def draft_email(self, recipient: str, subject: str, content: str, tone: str = "professional") -> StepResult[EmailObservation]:  
        """Draft a personalized email."""  
        return await self.step(EmailAction(  
            action_type="draft_email",  
            draft_recipient=recipient,  
            draft_subject=subject,  
            draft_content=content,  
            tone=tone  
        ))  
  
    async def organize_emails(self, criteria: Dict = None, priority_filter: str = None) -> StepResult[EmailObservation]:  
        """Organize emails based on criteria."""  
        return await self.step(EmailAction(  
            action_type="organize_emails",  
            organize_criteria=criteria,  
            priority_filter=priority_filter  
        ))  
  
    async def auto_respond(self, rules: Dict = None) -> StepResult[EmailObservation]:  
        """Generate automatic responses."""  
        return await self.step(EmailAction(  
            action_type="auto_respond",  
            auto_response_rules=rules  
        ))  
  
    async def get_thread_insights(self, thread_id: str) -> StepResult[EmailObservation]:  
        """Get insights for an email thread."""  
        return await self.step(EmailAction(  
            action_type="get_thread_insights",  
            thread_id=thread_id  
        ))  
  
    async def schedule_followup(self, email_id: str, delay_hours: int = 24, message: str = None) -> StepResult[EmailObservation]:  
        """Schedule a follow-up email."""  
        return await self.step(EmailAction(  
            action_type="schedule_followup",  
            followup_email_id=email_id,  
            followup_delay=delay_hours,  
            followup_message=message  
        ))  
  
    async def send_scheduled_emails(self) -> StepResult[EmailObservation]:  
        """Send all scheduled emails that are due."""  
        return await self.step(EmailAction(action_type="send_scheduled_emails"))
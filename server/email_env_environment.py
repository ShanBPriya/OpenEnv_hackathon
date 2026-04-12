# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

from uuid import uuid4  

from typing import List, Dict, Any, Optional  
import random  
from datetime import datetime, timedelta  
  
from openenv.core.env_server.interfaces import Environment  
from openenv.core.env_server.types import State  

try:
    from ..models import EmailAction, EmailObservation, EmailState
    from ..rubrics import EmailRubric
except ImportError:
    from models import EmailAction, EmailObservation, EmailState
    from rubrics import EmailRubric
  
  
class EmailEnvironment(Environment):  
    """Advanced email management environment with three distinct tasks."""  
  
    SUPPORTS_CONCURRENT_SESSIONS = True  
  
    def __init__(self):  
        super().__init__()  
        self._state = EmailState(episode_id=str(uuid4()), step_count=0)  
        self.emails: List[Dict] = []  
        self._ground_truth = {}  
        self.task = "basic_triage"  
        self._user_preferences = {  
            "tone": "professional",  
            "signature": "Best regards",  
            "response_delay": 24,  
        }  
        # Initialize rubric as required by RFC 004  
        self.rubric = EmailRubric()  
  
    def reset(self, task_name: Optional[str] = None, **kwargs) -> EmailObservation:  
        """Reset environment for a specific task."""  
        self._state = EmailState(  
            episode_id=str(uuid4()),   
            step_count=0,  
            task_name=task_name or "basic_triage"  
        )  
          
        # Select task  
        available_tasks = ["basic_triage", "thread_management", "advanced_workflow"]  
        self.task = task_name or random.choice(available_tasks)  
        self._state.task_name = self.task  
          
        # Reset rubric  
        self.rubric.reset()  
          
        # Generate task-specific emails  
        if self.task == "basic_triage":  
            self._setup_basic_triage()  
        elif self.task == "thread_management":  
            self._setup_thread_management()  
        else:  # advanced_workflow  
            self._setup_advanced_workflow()  
          
        return EmailObservation(  
            success=True,  
            emails=self.emails,  
            message=f"{self.task} task loaded with {len(self.emails)} emails",  
            metadata={"task_name": self.task},  
            reward=0.0,  
            done=False  
        )  
  
    def step(self, action: EmailAction) -> EmailObservation:  
        """Execute action and compute reward using rubric."""  
        self._state.step_count += 1  
        self._state.actions_history.append({  
            "step": self._state.step_count,  
            "action_type": action.action_type,  
            "timestamp": datetime.now().isoformat()  
        })  
  
        # Execute action  
        observation = self._execute_action(action)  
          
        # Compute reward using rubric  
        reward = self.rubric(action, observation)  
        observation.reward = reward  
          
        # Check completion  
        if self._check_completion():  
            observation.done = True  
            observation.metadata = observation.metadata or {}  
            observation.metadata["score"] = self._compute_final_score()  
            observation.message = "task completed"  
          
        return observation  
  
    def _execute_action(self, action: EmailAction) -> EmailObservation:  
        """Execute the action and return observation."""  
        if self._state.step_count > 25:  
            return EmailObservation(  
                success=False,  
                message="max steps reached",  
                reward=-0.5,  
                done=True  
            )  
  
        # Handle different action types  
        if action.action_type == "list_emails":  
            return EmailObservation(  
                success=True,  
                emails=self.emails,  
                message=f"listed {len(self.emails)} emails"  
            )  
  
        elif action.action_type == "read_email":  
            email = self._get_email(action.email_id)  
            if not email:  
                return EmailObservation(  
                    success=False,  
                    error_message="email not found"  
                )  
            email["is_read"] = True  
            return EmailObservation(  
                success=True,  
                current_email=email,  
                message="email read"  
            )  
  
        elif action.action_type == "classify_email":  
            return self._handle_classify_email(action)  
  
        elif action.action_type == "draft_email":  
            return self._handle_draft_email(action)  
  
        elif action.action_type == "organize_emails":  
            return self._handle_organize_emails(action)  
  
        elif action.action_type == "auto_respond":  
            return self._handle_auto_respond(action)  
  
        elif action.action_type == "get_thread_insights":  
            return self._handle_thread_insights(action)  
  
        elif action.action_type == "schedule_followup":  
            return self._handle_schedule_followup(action)  
  
        elif action.action_type in ["reply_email", "archive_email"]:  
            return EmailObservation(  
                success=True,  
                message=f"{action.action_type} completed"  
            )  
  
        else:  
            return EmailObservation(  
                success=False,  
                error_message="invalid action"  
            )  
  
    def _handle_classify_email(self, action: EmailAction) -> EmailObservation:  
        """Handle email classification with ground truth checking."""  
        email = self._get_email(action.email_id)  
        if not email:  
            return EmailObservation(  
                success=False,  
                error_message="email not found"  
            )  
  
        email["category"] = action.category  
        correct = self._ground_truth.get(email["id"])  
          
        if action.category == correct:  
            return EmailObservation(  
                success=True,  
                message="correct classification",  
                metadata={"classification_correct": True}  
            )  
        else:  
            return EmailObservation(  
                success=True,  
                message="wrong classification",  
                metadata={"classification_correct": False}  
            )  
  
    def _handle_draft_email(self, action: EmailAction) -> EmailObservation:  
        """Handle email drafting with personalization."""  
        draft = {  
            "id": f"draft_{len(self._state.drafts) + 1}",  
            "recipient": action.draft_recipient,  
            "subject": action.draft_subject,  
            "content": self._personalize_content(  
                action.draft_content,  
                action.tone or self._user_preferences["tone"]  
            ),  
            "timestamp": datetime.now().isoformat(),  
            "status": "draft"  
        }  
        self._state.drafts.append(draft)  
          
        return EmailObservation(  
            success=True,  
            draft_email=draft,  
            message="email drafted successfully"  
        )  
  
    def _handle_organize_emails(self, action: EmailAction) -> EmailObservation:  
        """Handle email organization."""  
        organized = self._organize_emails(  
            action.organize_criteria or {},  
            action.priority_filter  
        )  
          
        return EmailObservation(  
            success=True,  
            organized_emails=organized,  
            message=f"emails organized into {len(organized)} categories"  
        )  
  
    def _handle_auto_respond(self, action: EmailAction) -> EmailObservation:  
        """Handle automatic response generation."""  
        responses = self._generate_auto_responses(  
            action.auto_response_rules or {}  
        )  
          
        return EmailObservation(  
            success=True,  
            auto_responses=responses,  
            message=f"generated {len(responses)} auto responses"  
        )  
  
    def _handle_thread_insights(self, action: EmailAction) -> EmailObservation:  
        """Handle thread analysis."""  
        insights = self._analyze_thread(action.thread_id)  
          
        return EmailObservation(  
            success=True,  
            thread_insights=insights,  
            message="thread analysis complete"  
        )  
  
    def _handle_schedule_followup(self, action: EmailAction) -> EmailObservation:  
        """Handle follow-up scheduling."""  
        followup = {  
            "id": f"followup_{len(self._state.scheduled_emails) + 1}",  
            "email_id": action.followup_email_id,  
            "scheduled_time": (datetime.now() + timedelta(hours=action.followup_delay or 24)).isoformat(),  
            "message": action.followup_message,  
            "status": "scheduled"  
        }  
        self._state.scheduled_emails.append(followup)  
          
        return EmailObservation(  
            success=True,  
            scheduled_followups=[followup],  
            message="follow-up scheduled"  
        )  
  
    # Task setup methods  
    def _setup_basic_triage(self):  
        """Setup basic email triage task."""  
        self.emails = [  
            {  
                "id": "1",   
                "subject": "Team Meeting",   
                "body": "Join meeting tomorrow",   
                "category": None,   
                "priority": "high",  
                "thread_id": "thread_1",  
                "sender": "boss@company.com",  
                "timestamp": datetime.now().isoformat(),  
                "is_read": False  
            },  
            {  
                "id": "2",   
                "subject": "SALE!!!",   
                "body": "Buy now",   
                "category": None,   
                "priority": "low",  
                "thread_id": "thread_2",  
                "sender": "spam@fake.com",  
                "timestamp": datetime.now().isoformat(),  
                "is_read": False  
            },  
        ]  
        self._ground_truth = {"1": "important", "2": "spam"}  
  
    def _setup_thread_management(self):  
        """Setup thread management task with email threads."""  
        self.emails = [  
            {  
                "id": "1",   
                "subject": "Re: Project Update",   
                "body": "Thanks for the update",   
                "category": None,   
                "priority": "medium",  
                "thread_id": "thread_proj",  
                "sender": "client@company.com",  
                "timestamp": datetime.now().isoformat(),  
                "is_read": False  
            },  
            {  
                "id": "2",   
                "subject": "Re: Project Update",   
                "body": "Looking forward to it",   
                "category": None,   
                "priority": "medium",  
                "thread_id": "thread_proj",  
                "sender": "boss@company.com",  
                "timestamp": datetime.now().isoformat(),  
                "is_read": False  
            },  
        ]  
        self._ground_truth = {"1": "work", "2": "work"}  
  
    def _setup_advanced_workflow(self):  
        """Setup advanced workflow task."""  
        self.emails = [  
            {  
                "id": "1",   
                "subject": "Invoice #1234",   
                "body": "Payment due next week",   
                "category": None,   
                "priority": "high",  
                "thread_id": "thread_invoice",  
                "sender": "billing@vendor.com",  
                "timestamp": datetime.now().isoformat(),  
                "is_read": False  
            },  
            {  
                "id": "2",   
                "subject": "Newsletter",   
                "body": "Check out our latest updates",   
                "category": None,   
                "priority": "low",  
                "thread_id": "thread_news",  
                "sender": "newsletter@company.com",  
                "timestamp": datetime.now().isoformat(),  
                "is_read": False  
            },  
        ]  
        self._ground_truth = {"1": "finance", "2": "promotion"}  
  
    # Helper methods  
    def _personalize_content(self, content: str, tone: str) -> str:  
        """Personalize email content based on user preferences."""  
        tone_modifiers = {  
            "formal": "Dear",  
            "casual": "Hi",  
            "friendly": "Hey",  
            "professional": "Dear"  
        }  
          
        greeting = tone_modifiers.get(tone, "Hi")  
        signature = self._user_preferences["signature"]  
          
        return f"{greeting},\n\n{content}\n\n{signature}"  
  
    def _organize_emails(self, criteria: Dict, priority_filter: Optional[str]) -> Dict:  
        """Organize emails based on criteria."""  
        organized = {  
            "urgent": [],  
            "high": [],  
            "medium": [],  
            "low": [],  
            "unclassified": []  
        }  
          
        for email in self.emails:  
            priority = email.get("priority", "medium")  
            if priority_filter and priority != priority_filter:  
                continue  
                  
            if priority in organized:  
                organized[priority].append(email)  
            else:  
                organized["unclassified"].append(email)  
                  
        return organized  
  
    def _generate_auto_responses(self, rules: Dict) -> List[Dict]:  
        """Generate automatic responses for routine inquiries."""  
        responses = []  
          
        for email in self.emails:  
            if email.get("category") == "spam" or email.get("is_read"):  
                continue  
                  
            # Simple auto-response logic  
            if "meeting" in email.get("subject", "").lower():  
                response = {  
                    "to": email["sender"],  
                    "subject": f"Re: {email['subject']}",  
                    "body": "Thank you for the meeting invitation. I will confirm my attendance shortly.",  
                    "type": "auto_response"  
                }  
                responses.append(response)  
                  
        return responses  
  
    def _analyze_thread(self, thread_id: str) -> Dict:  
        """Analyze email thread and provide insights."""  
        thread_emails = [e for e in self.emails if e.get("thread_id") == thread_id]  
          
        if not thread_emails:  
            return {"error": "thread not found"}  
              
        # Simple thread analysis  
        insights = {  
            "thread_id": thread_id,  
            "message_count": len(thread_emails),  
            "participants": list(set(e.get("sender", "") for e in thread_emails)),  
            "last_activity": max(e.get("timestamp", "") for e in thread_emails),  
            "summary": f"Thread with {len(thread_emails)} messages",  
            "actionable_items": [],  
            "next_steps": "Review and respond to latest message"  
        }  
          
        # Store summary  
        self._state.thread_summaries[thread_id] = insights["summary"]  
          
        return insights  
  
    def _check_completion(self) -> bool:  
        """Check if the current task is completed."""  
        if self.task == "basic_triage":  
            return all(e.get("category") for e in self.emails)  
        elif self.task == "thread_management":  
            return len(self._state.scheduled_emails) > 0 and len(self._state.thread_summaries) > 0  
        elif self.task == "advanced_workflow":  
            return len(self._state.drafts) > 0 and len(self._state.scheduled_emails) > 0  
        return False  
  
    def _compute_final_score(self) -> float:  
        """Compute final score for the episode."""  
        if self.task == "basic_triage":  
            total = len(self.emails)  
            correct = sum(  
                1 for e in self.emails  
                if e.get("category") == self._ground_truth.get(e["id"])  
            )  
            return correct / total if total > 0 else 1.0  
        else:  
            # For other tasks, score based on completion  
            score = 0.0  
            if len(self._state.drafts) > 0:  
                score += 0.3  
            if len(self._state.scheduled_emails) > 0:  
                score += 0.3  
            if len(self._state.thread_summaries) > 0:  
                score += 0.4  
            return score  
  
    def _get_email(self, email_id: str) -> Optional[Dict]:  
        """Get email by ID."""  
        for e in self.emails:  
            if e["id"] == email_id:  
                return e  
        return None  
  
    @property  
    def state(self) -> EmailState:  
        """Get current environment state."""  
        return self._state
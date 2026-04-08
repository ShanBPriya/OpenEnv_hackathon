# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""
Email Env Environment Implementation.

"""

from uuid import uuid4
from typing import List, Dict
import random

from openenv.core.env_server.interfaces import Environment
from openenv.core.env_server.types import State

from ..models import EmailAction, EmailObservation


class EmailEnvironment(Environment):

    SUPPORTS_CONCURRENT_SESSIONS = True

    def __init__(self):
        self._state = State(episode_id=str(uuid4()), step_count=0)
        self.emails: List[Dict] = []
        self._ground_truth = {}
        self.task = "easy"

    def reset(self) -> EmailObservation:
        self._state = State(episode_id=str(uuid4()), step_count=0)

        self.task = random.choice(["easy", "medium", "hard"])

        if self.task == "easy":
            self.emails = [
                {"id": "1", "subject": "Meeting", "body": "Join meeting", "category": None, "priority": "high"},
                {"id": "2", "subject": "SALE!!!", "body": "Buy now", "category": None, "priority": "low"},
            ]
            self._ground_truth = {"1": "important", "2": "spam"}

        elif self.task == "medium":
            self.emails = [
                {"id": "1", "subject": "Invoice reminder", "body": "Payment due", "category": None, "priority": "high"},
                {"id": "2", "subject": "Discount offer", "body": "Limited time", "category": None, "priority": "low"},
            ]
            self._ground_truth = {"1": "important", "2": "promotion"}

        else:  # hard
            self.emails = [
                {"id": "1", "subject": "URGENT: Account issue", "body": "Verify now", "category": None, "priority": "high"},
                {"id": "2", "subject": "Win prize", "body": "Click link now", "category": None, "priority": "low"},
            ]
            self._ground_truth = {"1": "important", "2": "spam"}

        return EmailObservation(
            success=True,
            emails=self.emails,
            message=f"{self.task} task loaded",
            reward=0.0,
            done=False,
        )

    def step(self, action: EmailAction) -> EmailObservation:
        self._state.step_count += 1

        # prevent infinite loops
        if self._state.step_count > 10:
            return EmailObservation(success=True, done=True, reward=0.0)

        if action.action_type == "list_emails":
            return EmailObservation(success=True, emails=self.emails, reward=0.1, done=False)

        elif action.action_type == "read_email":
            email = self._get_email(action.email_id)
            if not email:
                return EmailObservation(success=False, error_message="email not found", reward=-1.0, done=False)
            return EmailObservation(success=True, current_email=email, reward=0.2, done=False)

        elif action.action_type == "classify_email":
            email = self._get_email(action.email_id)
            if not email:
                return EmailObservation(success=False, error_message="email not found", reward=-1.0, done=False)

            email["category"] = action.category

            correct = self._ground_truth.get(email["id"])
            reward = 1.0 if action.category == correct else -1.0

        elif action.action_type == "reply_email":
            email = self._get_email(action.email_id)
            if not email:
                return EmailObservation(success=False, error_message="email not found", reward=-1.0, done=False)

            reward = 0.5 if email["priority"] == "high" else -0.5

        elif action.action_type == "archive_email":
            self.emails = [e for e in self.emails if e["id"] != action.email_id]
            reward = 0.3

        else:
            return EmailObservation(success=False, error_message="invalid action", reward=-1.0, done=False)

        # completion check
        if all(e.get("category") for e in self.emails):
            score = self.compute_score()

            return EmailObservation(
                success=True,
                message="task completed",
                reward=score,
                done=True,
                metadata={"score": score},
            )

        return EmailObservation(success=True, reward=reward, done=False)

    def compute_score(self):
        total = len(self.emails)
        correct = sum(
            1 for e in self.emails
            if e.get("category") == self._ground_truth.get(e["id"])
        )
        return correct / total if total > 0 else 1.0

    def _get_email(self, email_id: str):
        for e in self.emails:
            if e["id"] == email_id:
                return e
        return None

    @property
    def state(self) -> State:
        return self._state
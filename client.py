# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""Email Env Environment Client."""

from typing import Dict

from openenv.core import EnvClient
from openenv.core.client_types import StepResult
from openenv.core.env_server.types import State

from .models import EmailAction, EmailObservation


class EmailEnv(EnvClient[EmailAction, EmailObservation, State]):

    def _step_payload(self, action: EmailAction) -> Dict:
        return {
            "action_type": action.action_type,
            "email_id": action.email_id,
            "category": action.category,
            "reply_content": action.reply_content,
        }

    def _parse_result(self, payload: Dict) -> StepResult[EmailObservation]:
        obs_data = payload.get("observation", {})

        observation = EmailObservation(
            success=obs_data.get("success", True),
            error_message=obs_data.get("error_message"),
            emails=obs_data.get("emails"),
            current_email=obs_data.get("current_email"),
            message=obs_data.get("message"),
            done=payload.get("done", False),
            reward=payload.get("reward"),
            metadata=obs_data.get("metadata", {}),
        )

        return StepResult(
            observation=observation,
            reward=payload.get("reward"),
            done=payload.get("done", False),
        )

    def _parse_state(self, payload: Dict) -> State:
        return State(
            episode_id=payload.get("episode_id"),
            step_count=payload.get("step_count", 0),
        )
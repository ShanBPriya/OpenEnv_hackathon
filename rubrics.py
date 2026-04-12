"""Email environment rubrics for reward computation following RFC 004."""  
# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

  
from typing import List, Tuple, Any, Dict  
from openenv.core.rubrics.trajectory import ExponentialDiscountingTrajectoryRubric  
  
  
class BasicTriageRubric(ExponentialDiscountingTrajectoryRubric):  
    """Rubric for basic email triage task.  
      
    Success criteria:  
    - Correctly classify all emails (0.0-1.0)  
    - Bonus for efficiency (fewer steps)  
    - Penalty for incorrect classifications  
    """  
  
    def __init__(self, gamma: float = 0.95):  
        super().__init__(gamma=gamma, intermediate_reward=0.0)  
  
    def score_trajectory(self, trajectory: List[Tuple[Any, Any]]) -> float:  
        """Score based on classification accuracy and efficiency."""  
        if not trajectory:  
            return 0.0  
          
        _, final_obs = trajectory[-1]  
        metadata = getattr(final_obs, 'metadata', {})  
          
        # Base score from classification accuracy  
        base_score = metadata.get('score', 0.0)  
          
        # Efficiency bonus (fewer steps = higher score)  
        step_count = len(trajectory)  
        efficiency_bonus = max(0, (20 - step_count) / 20) * 0.1  
          
        # Penalty for errors  
        error_count = sum(1 for _, obs in trajectory   
                         if not getattr(obs, 'success', True))  
        error_penalty = error_count * 0.1  
          
        final_score = base_score + efficiency_bonus - error_penalty  
        return max(0.0, min(1.0, final_score))  
  
  
class ThreadManagementRubric(ExponentialDiscountingTrajectoryRubric):  
    """Rubric for email thread management task.  
      
    Success criteria:  
    - Analyze threads correctly (0.0-0.5)  
    - Schedule appropriate follow-ups (0.0-0.3)  
    - Generate insights (0.0-0.2)  
    """  
  
    def __init__(self, gamma: float = 0.95):  
        super().__init__(gamma=gamma, intermediate_reward=0.0)  
  
    def score_trajectory(self, trajectory: List[Tuple[Any, Any]]) -> float:  
        """Score based on thread analysis and follow-up management."""  
        if not trajectory:  
            return 0.0  
          
        score = 0.0  
          
        # Check for thread analysis  
        thread_analyzed = any(  
            getattr(action, 'action_type', None) == 'get_thread_insights'  
            for action, _ in trajectory  
        )  
        if thread_analyzed:  
            score += 0.5  
          
        # Check for follow-up scheduling  
        followup_scheduled = any(  
            getattr(action, 'action_type', None) == 'schedule_followup'  
            for action, _ in trajectory  
        )  
        if followup_scheduled:  
            score += 0.3  
          
        # Check for insights generation  
        insights_generated = any(  
            getattr(obs, 'thread_insights', None) is not None  
            for _, obs in trajectory  
        )  
        if insights_generated:  
            score += 0.2  
          
        return score  
  
  
class AdvancedWorkflowRubric(ExponentialDiscountingTrajectoryRubric):  
    """Rubric for advanced email workflow task.  
      
    Success criteria:  
    - Draft personalized emails (0.0-0.3)  
    - Organize emails effectively (0.0-0.3)  
    - Auto-respond appropriately (0.0-0.2)  
    - Complete workflow efficiently (0.0-0.2)  
    """  
  
    def __init__(self, gamma: float = 0.95):  
        super().__init__(gamma=gamma, intermediate_reward=0.0)  
  
    def score_trajectory(self, trajectory: List[Tuple[Any, Any]]) -> float:  
        """Score based on advanced workflow completion."""  
        if not trajectory:  
            return 0.0  
          
        score = 0.0  
        action_types = set()  
          
        # Track different action types  
        for action, _ in trajectory:  
            action_types.add(getattr(action, 'action_type', None))  
          
        # Score for drafting emails  
        if 'draft_email' in action_types:  
            score += 0.3  
          
        # Score for organizing emails  
        if 'organize_emails' in action_types:  
            score += 0.3  
          
        # Score for auto-responses  
        if 'auto_respond' in action_types:  
            score += 0.2  
          
        # Efficiency bonus  
        if len(trajectory) <= 15:  
            score += 0.2  
          
        return score  
  
  
class EmailRubric:  
    """Main rubric that dispatches to task-specific rubrics."""  
      
    def __init__(self):  
        self.basic_triage = BasicTriageRubric()  
        self.thread_management = ThreadManagementRubric()  
        self.advanced_workflow = AdvancedWorkflowRubric()  
        self._current_rubric = None  
        self._trajectory = []  
  
    def __call__(self, action, observation) -> float:  
        """Compute reward based on current task."""  
        self._trajectory.append((action, observation))  
          
        # Get task name from state or observation  
        task_name = getattr(observation, 'metadata', {}).get('task_name', 'basic_triage')  
          
        # Select appropriate rubric  
        if task_name == 'basic_triage':  
            self._current_rubric = self.basic_triage  
        elif task_name == 'thread_management':  
            self._current_rubric = self.thread_management  
        elif task_name == 'advanced_workflow':  
            self._current_rubric = self.advanced_workflow  
        else:  
            self._current_rubric = self.basic_triage  
          
        # Compute intermediate rewards for partial progress  
        intermediate_reward = self._compute_intermediate_reward(action, observation)  
          
        # Return final reward if done, otherwise intermediate  
        if getattr(observation, 'done', False):  
            return self._current_rubric.score_trajectory(self._trajectory)  
        else:  
            return intermediate_reward  
  
    def _compute_intermediate_reward(self, action, observation) -> float:  
        """Provide partial progress rewards."""  
        action_type = getattr(action, 'action_type', None)  
          
        # Small rewards for productive actions  
        if action_type in ['classify_email', 'draft_email', 'organize_emails']:  
            if getattr(observation, 'success', False):  
                return 0.1  
        elif action_type in ['read_email', 'list_emails']:  
            return 0.05  
          
        # Penalties for errors  
        if not getattr(observation, 'success', True):  
            return -0.2  
          
        return 0.0  
  
    def reset(self):  
        """Reset rubric state."""  
        self._trajectory = []  
        self._current_rubric = None  
        if hasattr(self.basic_triage, 'reset'):  
            self.basic_triage.reset()  
        if hasattr(self.thread_management, 'reset'):  
            self.thread_management.reset()  
        if hasattr(self.advanced_workflow, 'reset'):  
            self.advanced_workflow.reset()
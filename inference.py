#!/usr/bin/env python3
# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

import argparse
import asyncio
import random
from typing import Any, List

from email_environ import EmailAction, EmailEnv
  
  
# Configuration constants  
MAX_EPISODE_STEPS = 25  
SUCCESS_SCORE_THRESHOLD = 0.7  
MAX_TOTAL_REWARD = 10.0  # Maximum possible reward per episode  
  
  
def log_start(task_name: str, episode_id: str):  
    """Log the start of an episode."""  
    print(f"[START] Task: {task_name}, Episode: {episode_id}", flush=True)  
  
  
def log_step(step: int, action_type: str, reward: float, done: bool):  
    """Log each step."""  
    print(f"[STEP {step}] Action: {action_type}, Reward: {reward:.3f}, Done: {done}", flush=True)  
  
  
def log_end(success: bool, steps: int, score: float, rewards: List[float]):  
    """Log the end of an episode."""  
    total_reward = sum(rewards)
    avg_reward = (total_reward / len(rewards)) if rewards else 0.0
    print(f"[END] Success: {success}, Steps: {steps}, Score: {score:.3f}", flush=True)  
    print(f"[REWARDS] Total: {total_reward:.3f}, Avg: {avg_reward:.3f}", flush=True)  
  
  
async def run_episode(env: EmailEnv, task_name: str, episode_id: str) -> tuple[bool, int, float, List[float]]:  
    """Run a single episode of the email environment."""  
    log_start(task_name, episode_id)  
      
    # Reset environment with specific task  
    result = await env.reset(task_name=task_name)  
    obs = result.observation  
    steps_taken = 0  
    rewards = []  
      
    # Simple agent logic - you can replace this with your actual agent  
    while not result.done and steps_taken < MAX_EPISODE_STEPS:  
        steps_taken += 1  
          
        # Choose action based on task and current state  
        action = await choose_action(env, obs, task_name, steps_taken)  
          
        # Execute action  
        result = await env.step(action)  
        obs = result.observation  
        reward = result.reward or 0.0  
        rewards.append(reward)  
          
        log_step(steps_taken, action.action_type, reward, result.done)  
          
        if result.done:  
            break  
      
    return False, steps_taken, 0.0, rewards  
  
  
async def choose_action(env: EmailEnv, obs: Any, task_name: str, step: int) -> EmailAction:  
    """Simple action selection logic - replace with your agent."""  
    emails = obs.emails or []  
      
    if task_name == "basic_triage":  
        # Classify unclassified emails  
        unclassified = [e for e in emails if not e.get("category")]  
        if unclassified:  
            email = unclassified[0]  
            # Simple heuristic based on subject  
            if "spam" in email.get("subject", "").lower() or "sale" in email.get("subject", "").lower():  
                category = "spam"  
            elif "urgent" in email.get("subject", "").lower() or "meeting" in email.get("subject", "").lower():  
                category = "important"  
            else:  
                category = "promotion"  
              
            return EmailAction(  
                action_type="classify_email",  
                email_id=email["id"],  
                category=category  
            )  
      
    elif task_name == "thread_management":  
        # Analyze threads and schedule follow-ups  
        if step <= 5:  
            # First, list and read emails  
            if emails:  
                return EmailAction(action_type="list_emails")  
        else:  
            # Schedule follow-up for high priority emails  
            high_priority = [e for e in emails if e.get("priority") == "high"]  
            if high_priority:  
                return EmailAction(  
                    action_type="schedule_followup",  
                    followup_email_id=high_priority[0]["id"],  
                    followup_delay=24,  
                    followup_message="Following up on this important email"  
                )  
      
    elif task_name == "advanced_workflow":  
        # Complete workflow: organize, draft, auto-respond  
        if step == 1:  
            return EmailAction(action_type="organize_emails")  
        elif step == 2:  
            return EmailAction(  
                action_type="draft_email",  
                draft_recipient="team@company.com",  
                draft_subject="Weekly Update",  
                draft_content="Here's our weekly progress update...",  
                tone="professional"  
            )  
        elif step == 3:  
            return EmailAction(action_type="auto_respond")  
      
    # Default action  
    return EmailAction(action_type="list_emails")  
  
  
async def main():  
    """Main inference loop."""  
    parser = argparse.ArgumentParser(description="Email Environment Inference")  
    parser.add_argument("--base-url", default="ws://localhost:8000", help="Environment server URL")  
    parser.add_argument("--episodes", type=int, default=10, help="Number of episodes to run")  
    parser.add_argument("--task", choices=["basic_triage", "thread_management", "advanced_workflow", "random"],   
                       default="random", help="Task to run")  
    parser.add_argument("--seed", type=int, default=42, help="Random seed")  
      
    args = parser.parse_args()  
      
    # Set random seed  
    random.seed(args.seed)  
      
    # Task selection  
    tasks = ["basic_triage", "thread_management", "advanced_workflow"]  
    if args.task == "random":  
        task_sequence = [random.choice(tasks) for _ in range(args.episodes)]  
    else:  
        task_sequence = [args.task] * args.episodes  
      
    print(f"[INFO] Starting {args.episodes} episodes with tasks: {task_sequence}", flush=True)  
      
    # Statistics  
    total_successes = 0  
    total_episodes = 0  
    all_scores = []  
      
    for episode_idx in range(args.episodes):  
        task_name = task_sequence[episode_idx]  
        episode_id = f"ep_{episode_idx}_{task_name}"  
          
        env = EmailEnv(base_url=args.base_url)  
          
        try:  
            success, steps_taken, score, rewards = await run_episode(env, task_name, episode_id)  
              
            # Calculate final score using your logic  
            score = sum(rewards) / MAX_TOTAL_REWARD if MAX_TOTAL_REWARD > 0 else 0.0  
            score = min(max(score, 0.0), 1.0)  # clamp to [0, 1]  
            success = score >= SUCCESS_SCORE_THRESHOLD  
              
            total_successes += 1 if success else 0  
            total_episodes += 1  
            all_scores.append(score)  
              
        except Exception as e:  
            print(f"[ERROR] Episode {episode_id} failed: {e}", flush=True)  
            success = False  
            steps_taken = 0  
            score = 0.0  
            rewards = []  
          
        finally:  
            try:  
                await env.close()  
            except Exception as e:  
                print(f"[DEBUG] env.close() error (container cleanup): {e}", flush=True)  
            log_end(success=success, steps=steps_taken, score=score, rewards=rewards)  
      
    # Final statistics  
    if total_episodes > 0:  
        success_rate = total_successes / total_episodes  
        avg_score = sum(all_scores) / len(all_scores)  
        print(f"\n[SUMMARY] Episodes: {total_episodes}, Success Rate: {success_rate:.2%}, Avg Score: {avg_score:.3f}", flush=True)  
  
  
if __name__ == "__main__":  
    asyncio.run(main())
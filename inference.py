import asyncio
import os
import json
from typing import List, Optional

from openai import OpenAI
from pydantic import ValidationError
from email_env1 import EmailEnv, EmailAction

API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")
API_KEY = os.getenv("HF_API_KEY") or os.getenv("OPENAI_API_KEY")
IMAGE_NAME = os.getenv("IMAGE_NAME", "email_env:latest")

MAX_STEPS = 10


def log_start(task, env, model):
    print(f"[START] task={task} env={env} model={model}", flush=True)


def log_step(step, action, reward, done, error):
    print(f"[STEP] step={step} action={action} reward={reward:.2f} done={str(done).lower()} error={error or 'null'}", flush=True)


def log_end(success, steps, score, rewards):
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(f"[END] success={str(success).lower()} steps={steps} score={score:.3f} rewards={rewards_str}", flush=True)


SYSTEM_PROMPT = """You are an email assistant. Output valid JSON actions with action_type one of: list_emails, read_email, classify_email, reply_email, archive_email.
Include relevant fields like email_id, category, reply_content as needed. For example:
{"action_type": "list_emails"}
{"action_type": "read_email", "email_id": "1"}
{"action_type": "classify_email", "email_id": "1", "category": "work"}
{"action_type": "reply_email", "email_id": "1", "reply_content": "Thank you"}
{"action_type": "archive_email", "email_id": "1"}"""



def get_action(client, obs):
    try:
        res = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": json.dumps(obs)},
            ],
            temperature=0.3,
        )
        return json.loads(res.choices[0].message.content)
    except Exception as exc:
        print(f"[ERROR] get_action failed: {exc}", flush=True)
        return {"action_type": "list_emails"}


def normalize_action_dict(action_dict):
    if not isinstance(action_dict, dict):
        return {"action_type": "list_emails"}

    normalized = dict(action_dict)
    if "action" in normalized and "action_type" not in normalized:
        normalized["action_type"] = normalized.pop("action")

    # Map common model outputs to valid action_types
    action_mapping = {
        "categorize": "classify_email",
        "categorize_emails": "classify_email",
        "search_email": "list_emails",
        "search_emails": "list_emails",
        "read": "read_email",
        "classify": "classify_email",
        "reply": "reply_email",
        "archive": "archive_email",
    }
    if normalized.get("action_type") in action_mapping:
        normalized["action_type"] = action_mapping[normalized["action_type"]]

    # Normalize categories
    category_mapping = {
        "urgent": "important",
        "important": "important",
        "spam": "spam",
        "promotion": "promotion",
        "promotions": "promotion",
        "work": "important",
        "personal": "important",
    }
    if "category" in normalized and normalized["category"] in category_mapping:
        normalized["category"] = category_mapping[normalized["category"]]

    # Ensure action_type is valid, else fallback
    valid_actions = {"list_emails", "read_email", "classify_email", "reply_email", "archive_email"}
    if normalized.get("action_type") not in valid_actions:
        normalized["action_type"] = "list_emails"

    allowed_keys = {"action_type", "email_id", "category", "reply_content"}
    return {k: v for k, v in normalized.items() if k in allowed_keys}


async def main():
    if not API_KEY:
        raise EnvironmentError(
            "HF_API_KEY or OPENAI_API_KEY is required. "
            "Set HF_API_KEY to your Hugging Face API token before running."
        )

    client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)
    env = await EmailEnv.from_docker_image(IMAGE_NAME)

    rewards = []
    steps = 0
    success = False

    log_start("email_triage", "email_env", MODEL_NAME)

    try:
        result = await env.reset()

        for step in range(1, MAX_STEPS + 1):
            if result.done:
                break

            obs = result.observation.model_dump()
            action_dict = normalize_action_dict(get_action(client, obs))
            try:
                action = EmailAction(**action_dict)
            except ValidationError as exc:
                print(f"[ERROR] invalid action payload: {action_dict} -> {exc}", flush=True)
                action = EmailAction(action_type="list_emails")

            result = await env.step(action)

            reward = result.reward or 0.0
            rewards.append(reward)
            steps = step

            log_step(step, str(action_dict), reward, result.done, None)

            if result.done:
                break

        # Use the final reward from environment if done, else sum rewards / 10
        if result.done and result.reward is not None:
            score = result.reward
        else:
            score = min(max(sum(rewards) / 10.0, 0.0), 1.0)
        success = score > 0.6

    finally:
        await env.close()
        log_end(success, steps, score, rewards)


if __name__ == "__main__":
    asyncio.run(main())
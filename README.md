---
title: Email Management Environment
emoji: 📧
colorFrom: blue
colorTo: purple
sdk: docker
pinned: false
app_port: 8000
base_path: /web
tags:
  - openenv
  - email
  - nlp
  - productivity
---

# Email Management Environment

Advanced email triage and management environment with drafting, organizing, and scheduling capabilities. This OpenEnv environment supports three distinct tasks: basic email triage, thread management, and advanced email workflows.

## Quick Start

The simplest way to use the Email Management environment is through the `EmailEnv` class:

```python
import asyncio
from email_environ import EmailEnv, EmailAction

async def main():
    # Create environment from Docker image
    env = EmailEnv.from_docker_image("email_environ:latest")
    
    try:
        # Reset environment for a specific task
        result = await env.reset(task_name="basic_triage")
        print(f"Task loaded: {result.observation.message}")
        print(f"Emails available: {len(result.observation.emails)}")
        
        # Execute an action (classify an email)
        action = EmailAction(
            action_type="classify_email",
            email_id="1",
            category="important"
        )
        result = await env.step(action)
        print(f"Action result: {result.observation.message}")
        print(f"Reward: {result.reward}")
        
    finally:
        await env.close()

if __name__ == "__main__":
    asyncio.run(main())
```

The `EmailEnv.from_docker_image()` method handles:
- Building/starting the Docker container
- Waiting for the server to be ready
- Establishing WebSocket connection
- Container cleanup when you call `close()`

## Building the Docker Image

Before using the environment, build the Docker image:

```bash
# From project root
docker build -t email_environ:latest -f dockerfile .
```

## Available Tasks

The environment supports three difficulty levels:

### 1. Basic Triage (Easy)
Classify incoming emails into categories (important, spam, promotion, etc.)

### 2. Thread Management (Medium)
Analyze email threads and schedule follow-up actions

### 3. Advanced Workflow (Hard)
Complete email workflow with drafting, organizing, and auto-response generation

## Deploying to Hugging Face Spaces

Deploy using the `openenv push` command:

```bash
# From the environment directory (where openenv.yaml is located)
openenv push

# Or with options
openenv push --namespace my-org --private
```

After deployment, your space will be available at:
`https://huggingface.co/spaces/<your-username>/email_environ`

The deployed space includes:
- **Web Interface** at `/web` - Interactive UI for exploring the environment
- **API Documentation** at `/docs` - Full OpenAPI/Swagger interface
- **Health Check** at `/health` - Container health monitoring
- **WebSocket** at `/ws` - Persistent session endpoint

## Environment Details

### EmailAction
Contains configuration for email management operations:
- `action_type` - Type of action (list_emails, classify_email, draft_email, etc.)
- `email_id` - ID of the email to operate on
- `category` - Category for classification
- `draft_content` - Content for drafting emails
- `organize_criteria` - Criteria for organizing emails
- `thread_id` - ID of email thread for analysis
- And more fields for advanced features

### EmailObservation
Contains the response data and metadata:
- `success` - Whether the action succeeded
- `emails` - List of emails in the inbox
- `current_email` - Currently viewed email
- `draft_email` - Drafted email response
- `organized_emails` - Emails organized by criteria
- `thread_insights` - Analysis of email thread
- `scheduled_followups` - Scheduled follow-ups
- `reward` - Computed reward for the action
- `done` - Whether the task is complete

### Reward
Rewards are computed using task-specific rubrics that follow OpenEnv RFC 004:
- **Basic Triage**: Based on classification accuracy with efficiency bonus
- **Thread Management**: Points for analyzing threads and scheduling follow-ups
- **Advanced Workflow**: Points for drafting, organizing, and auto-responding

## Advanced Usage

### Connecting to an Existing Server

If you already have an environment server running:

```python
from email_environ import EmailEnv, EmailAction
import asyncio

async def main():
    # Connect to existing server
    env = EmailEnv(base_url="http://localhost:8000")
    
    result = await env.reset(task_name="basic_triage")
    print(result.observation.emails)
    
    await env.close()

asyncio.run(main())
```

### Using Convenience Methods

The client provides helper methods for common actions:

```python
import asyncio
from email_environ import EmailEnv

async def main():
    env = EmailEnv(base_url="http://localhost:8000")
    
    # List emails
    result = await env.list_emails()
    
    # Read specific email
    result = await env.read_email(email_id="1")
    
    # Classify email
    result = await env.classify_email(
        email_id="1",
        category="important"
    )
    
    # Draft email
    result = await env.draft_email(
        recipient="team@company.com",
        subject="Weekly Update",
        content="Summary of this week...",
        tone="professional"
    )
    
    # Organize emails
    result = await env.organize_emails(
        criteria={"by": "priority"},
        priority_filter="high"
    )
    
    # Schedule follow-up
    result = await env.schedule_followup(
        email_id="1",
        delay_hours=24,
        message="Follow up on this email"
    )
    
    await env.close()

asyncio.run(main())
```

### Using Context Manager

The client supports context manager for automatic resource management:

```python
import asyncio
from email_environ import EmailEnv, EmailAction

async def main():
    async with EmailEnv(base_url="http://localhost:8000") as env:
        result = await env.reset()
        
        # Multiple steps with persistent session
        for i in range(5):
            action = EmailAction(action_type="list_emails")
            result = await env.step(action)
            print(f"Step {i}: {result.observation.message}")

asyncio.run(main())
```

### Running Inference

Run episodes with the inference script:

```bash
# Run 10 episodes of random tasks
python -m email_environ.inference --episodes 10

# Run specific task
python -m email_environ.inference --task basic_triage --episodes 5

# Set random seed for reproducibility
python -m email_environ.inference --seed 42
```

Options:
- `--base-url`: Environment server URL (default: ws://localhost:8000)
- `--episodes`: Number of episodes to run (default: 10)
- `--task`: Task to run - basic_triage, thread_management, advanced_workflow, random (default: random)
- `--seed`: Random seed for reproducibility

## Running Locally

### Start the Environment Server

```bash
# Option 1: Using uv (recommended)
uv run --project . server

# Option 2: Using Python directly
python -m email_environ.server.app --port 8000

# Option 3: Using uvicorn
uvicorn email_environ.server.app:app --reload --port 8000
```

The server will be available at `http://localhost:8000`

### Run Inference Against Local Server

```bash
python -m email_environ.inference --base-url http://localhost:8000 --episodes 5
```

## Project Structure

```
email_environ/
├── __init__.py                 # Package exports
├── client.py                   # EmailEnv client implementation
├── models.py                   # EmailAction, EmailObservation, EmailState
├── rubrics.py                  # Reward computation rubrics
├── inference.py                # Inference/evaluation script
├── dockerfile                  # Container image definition
├── openenv.yaml                # OpenEnv manifest
├── pyproject.toml              # Project metadata and dependencies
├── README.md                   # This file
└── server/
    ├── __init__.py             # Server exports
    ├── app.py                  # FastAPI application
    └── email_env_environment.py # Core environment logic
```

## Development & Testing

### Direct Environment Testing

Test the environment logic directly without the HTTP server:

```python
from email_environ.server.email_env_environment import EmailEnvironment
from email_environ.models import EmailAction

# Create environment
env = EmailEnvironment()

# Reset with a task
obs = env.reset(task_name="basic_triage")
print(f"Emails: {obs.emails}")

# Execute action
action = EmailAction(
    action_type="classify_email",
    email_id="1",
    category="important"
)
obs = env.step(action)
print(f"Reward: {obs.reward}")
```

### Testing with pytest

```bash
# Install dev dependencies
uv sync

# Run tests
pytest tests/
```

## Hackathon Compliance

This environment is designed with hackathon requirements in mind:

✅ **Open Source License**: BSD-style license (see LICENSE file)  
✅ **Proper Attribution**: Copyright notices in all source files  
✅ **Code Quality**: Type hints, docstrings, and clear structure  
✅ **Framework Compliance**: Follows OpenEnv RFC 004 for rubrics  
✅ **Documentation**: Comprehensive README with examples  
✅ **Reproducibility**: Seed-based randomization for consistent results  

## License

Copyright (c) Meta Platforms, Inc. and affiliates.

This source code is licensed under the BSD-style license found in the LICENSE file in the root directory of this source tree.

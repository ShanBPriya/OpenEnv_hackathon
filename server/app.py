"""FastAPI app for Email Environment."""  
# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

  
try:  
    from openenv.core.env_server.http_server import create_app  
except Exception as e:  
    raise ImportError(  
        "openenv is required for the web interface. Install dependencies with '\n    uv sync\n'"  
    ) from e  
  
try:  
    from email_environ.models import EmailAction, EmailObservation  
    from email_environ.server.email_env_environment import EmailEnvironment  
except ModuleNotFoundError:  
    from models import EmailAction, EmailObservation  
    from .email_env_environment import EmailEnvironment  
  
# Create the app with web interface and README integration  
app = create_app(  
    EmailEnvironment,  
    EmailAction,  
    EmailObservation,  
    env_name="email_environ",  
    max_concurrent_envs=5,  # Allow multiple concurrent sessions  
)  
  
  
def main(host: str = "0.0.0.0", port: int = 8000):  
    """Entry point for direct execution."""  
    import uvicorn  
    uvicorn.run(app, host=host, port=port)  
  
  
if __name__ == "__main__":  
    import argparse  
    parser = argparse.ArgumentParser()  
    parser.add_argument("--port", type=int, default=8000)  
    args = parser.parse_args()  
    main(port=args.port)
"""AWS Lambda entrypoint: the FastAPI app wrapped in Mangum.

Used by the ``lambda`` Docker stage, where ``awslambdaric`` invokes
``ddd_app.presentation.api.lambda_handler.handler``. Before the app (and its Settings) is built,
the database credentials are resolved from Secrets Manager: the ``api`` Terraform module injects
``DB_SECRET_ARN`` instead of baking the password into the Lambda environment.
"""

from __future__ import annotations

import json
import os

from mangum import Mangum

from ddd_app.core.config import get_settings
from ddd_app.core.telemetry import setup_telemetry
from ddd_app.presentation.api.app import create_app


def load_db_credentials_from_secret() -> None:
    """Populate DB_USER/DB_PASSWORD from the Secrets Manager secret, when DB_SECRET_ARN is set.

    The secret is the JSON ``{"username": ..., "password": ...}`` written by the secrets module.
    No-op outside AWS (local/dev read the credentials from .env directly).
    """
    arn = os.environ.get("DB_SECRET_ARN", "")
    if not arn:
        return
    import boto3  # imported lazily — only needed (and configured) on AWS

    payload = json.loads(
        boto3.client("secretsmanager").get_secret_value(SecretId=arn)["SecretString"]
    )
    os.environ["DB_USER"] = payload["username"]
    os.environ["DB_PASSWORD"] = payload["password"]


# Credentials must be in the environment before create_app() builds Settings.
load_db_credentials_from_secret()
app = create_app()
# No-op unless OTEL_ENABLE=true — point OTEL_EXPORTER_OTLP_ENDPOINT at a collector (e.g. ADOT).
setup_telemetry(app, get_settings())
# lifespan="off": create_app wires state synchronously, and Lambda has no reliable shutdown hook.
handler = Mangum(app, lifespan="off")

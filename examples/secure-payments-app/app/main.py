"""Small HTTP service used by the EKS defense-in-depth workshop."""

from datetime import timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os

import boto3
from botocore.exceptions import BotoCoreError, CredentialRetrievalError


HOST = "0.0.0.0"
PORT = int(os.environ.get("PORT", "8080"))
EXPECTED_CREDENTIAL_SOURCE = os.environ.get(
    "EXPECTED_CREDENTIAL_SOURCE", "container-role"
)


def identity_status() -> tuple[int, dict[str, object]]:
    """Confirm the Pod Identity provider issued credentials without exposing them."""
    try:
        credentials = boto3.Session().get_credentials()
        if credentials is None:
            return 503, {"status": "unavailable", "reason": "no AWS credentials found"}

        # Force the SDK to retrieve/refresh credentials, but never return key material.
        credentials.get_frozen_credentials()
        provider = credentials.method
        expiration = getattr(credentials, "_expiry_time", None)
        expires_at = None
        if expiration is not None:
            expires_at = expiration.astimezone(timezone.utc).isoformat()

        is_expected_provider = provider == EXPECTED_CREDENTIAL_SOURCE
        status = 200 if is_expected_provider else 503
        return status, {
            "status": "available" if is_expected_provider else "unexpected_provider",
            "provider": provider,
            "expected_provider": EXPECTED_CREDENTIAL_SOURCE,
            "expires_at": expires_at,
            "credential_values_returned": False,
        }
    except (BotoCoreError, CredentialRetrievalError):
        return 503, {"status": "unavailable", "reason": "credential provider could not refresh"}


class Handler(BaseHTTPRequestHandler):
    server_version = "SecurePaymentsWorkshop/1.0"

    def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
        if self.path == "/healthz":
            self._send_json(200, {"status": "ok"})
        elif self.path == "/readyz":
            self._send_json(200, {"status": "ready"})
        elif self.path == "/api/identity":
            status, body = identity_status()
            self._send_json(status, body)
        elif self.path == "/":
            self._send_json(
                200,
                {
                    "service": "secure-payments-workshop",
                    "message": "A minimal EKS sample protected by layered controls.",
                    "checks": ["/healthz", "/readyz", "/api/identity"],
                },
            )
        else:
            self._send_json(404, {"error": "not found"})

    def _send_json(self, status: int, body: dict[str, object]) -> None:
        payload = json.dumps(body, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, format_string: str, *args: object) -> None:
        # Keep routine request logs small; do not log headers or credentials.
        print(f"{self.log_date_time_string()} {self.address_string()} {args[0]}")


if __name__ == "__main__":
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()

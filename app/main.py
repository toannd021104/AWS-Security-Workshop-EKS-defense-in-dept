"""Three-tier workshop API, worker and one-shot database initializer."""
import json
import logging
import os
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import boto3
import psycopg
from psycopg.rows import dict_row

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
REGION = os.getenv("AWS_REGION", "us-east-1")
MODE = os.getenv("MODE", "api")


def connect(user=None, password=None):
    user = user or f"notes_{MODE}"
    host = os.environ["DB_HOST"]
    if password is None:
        password = boto3.client("rds", region_name=REGION).generate_db_auth_token(
            DBHostname=host, Port=5432, DBUsername=user)
    return psycopg.connect(host=host, port=5432, dbname="notes", user=user,
                           password=password, sslmode="verify-full",
                           sslrootcert="/app/rds-ca.pem", connect_timeout=5,
                           row_factory=dict_row)


def init_database():
    secret = boto3.client("secretsmanager", region_name=REGION).get_secret_value(
        SecretId=os.environ["DB_SECRET_ARN"])
    credentials = json.loads(secret["SecretString"])
    with connect(credentials["username"], credentials["password"]) as conn:
        conn.execute("CREATE SCHEMA IF NOT EXISTS notes")
        conn.execute("CREATE TABLE IF NOT EXISTS notes.entries (id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY, body text NOT NULL CHECK (length(body) BETWEEN 1 AND 1000))")
        conn.execute("CREATE TABLE IF NOT EXISTS notes.reports (id uuid PRIMARY KEY, note_count bigint NOT NULL, created_at timestamptz NOT NULL DEFAULT now())")
        for name in ("notes_api", "notes_worker"):
            if not conn.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", (name,)).fetchone():
                conn.execute(psycopg.sql.SQL("CREATE USER {} WITH LOGIN").format(psycopg.sql.Identifier(name)))
            conn.execute(psycopg.sql.SQL("GRANT rds_iam TO {}").format(psycopg.sql.Identifier(name)))
            conn.execute(psycopg.sql.SQL("GRANT CONNECT ON DATABASE notes TO {}").format(psycopg.sql.Identifier(name)))
            conn.execute(psycopg.sql.SQL("GRANT USAGE ON SCHEMA notes TO {}").format(psycopg.sql.Identifier(name)))
        conn.execute("GRANT SELECT, INSERT ON notes.entries TO notes_api")
        conn.execute("GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA notes TO notes_api")
        conn.execute("GRANT SELECT ON notes.reports TO notes_api")
        conn.execute("GRANT SELECT ON notes.entries TO notes_worker")
        conn.execute("GRANT INSERT, SELECT ON notes.reports TO notes_worker")
    logging.info("Database initialized with separate SQL roles; master secret was not printed.")


class Handler(BaseHTTPRequestHandler):
    def reply(self, code, body):
        data = json.dumps(body, default=str).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == "/healthz":
            return self.reply(200, {"status": "ok", "workload": "api"})
        queries = {"/notes": "SELECT id, body FROM notes.entries ORDER BY id DESC LIMIT 100",
                   "/reports": "SELECT * FROM notes.reports ORDER BY created_at DESC LIMIT 20"}
        if self.path not in queries:
            return self.reply(404, {"error": "not found"})
        try:
            with connect() as conn:
                return self.reply(200, conn.execute(queries[self.path]).fetchall())
        except Exception:
            logging.exception("Database request failed")
            return self.reply(503, {"error": "database unavailable"})

    def do_POST(self):
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if size < 0 or size > 4096:
                return self.reply(413, {"error": "payload too large"})
            payload = json.loads(self.rfile.read(size) or b"{}")
            if not isinstance(payload, dict):
                return self.reply(400, {"error": "JSON object required"})
            if self.path == "/notes":
                body = payload.get("body")
                if not isinstance(body, str) or not 1 <= len(body.strip()) <= 1000:
                    return self.reply(400, {"error": "body must have 1–1000 characters"})
                with connect() as conn:
                    row = conn.execute("INSERT INTO notes.entries (body) VALUES (%s) RETURNING id, body", (body.strip(),)).fetchone()
                return self.reply(201, row)
            if self.path == "/reports":
                task_id = str(uuid.uuid4())
                boto3.client("sqs", region_name=REGION).send_message(
                    QueueUrl=os.environ["QUEUE_URL"], MessageBody=json.dumps({"id": task_id}))
                return self.reply(202, {"id": task_id, "status": "queued"})
            return self.reply(404, {"error": "not found"})
        except (ValueError, TypeError):
            return self.reply(400, {"error": "invalid JSON"})
        except Exception:
            logging.exception("Application request failed")
            return self.reply(503, {"error": "dependency unavailable"})


def worker():
    sqs = boto3.client("sqs", region_name=REGION)
    queue = os.environ["QUEUE_URL"]
    while True:
        try:
            messages = sqs.receive_message(QueueUrl=queue, MaxNumberOfMessages=1, WaitTimeSeconds=20).get("Messages", [])
            for msg in messages:
                task_id = str(uuid.UUID(json.loads(msg["Body"])["id"]))
                with connect() as conn:
                    conn.execute("INSERT INTO notes.reports (id, note_count) SELECT %s, count(*) FROM notes.entries ON CONFLICT (id) DO NOTHING", (task_id,))
                sqs.delete_message(QueueUrl=queue, ReceiptHandle=msg["ReceiptHandle"])
                logging.info("Report completed: %s", task_id)
        except Exception:
            logging.exception("Worker dependency failed; message remains retryable")
            time.sleep(5)


if __name__ == "__main__":
    if MODE == "db-init":
        init_database()
    elif MODE == "worker":
        worker()
    else:
        ThreadingHTTPServer(("0.0.0.0", 8080), Handler).serve_forever()

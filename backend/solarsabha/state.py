"""Project state. Local JSON files for development, DynamoDB when running on AWS (STATE_BACKEND=dynamodb).

- Expiry: every project carries expires_at; expired projects read as missing (DynamoDB TTL deletes them on AWS).
- Optimistic locking: every project has a version. put() only succeeds if the stored version is still the one that
  was read, so a slow request can never overwrite a newer save; it raises ConflictError instead."""
import json, os, time, uuid
from pathlib import Path

class ConflictError(Exception):
    """The project was changed by someone else after it was read."""

def _next_version(doc: dict) -> tuple[int, int]:
    expected = int(doc.get("version", 0))
    return expected, expected + 1

class LocalStore:
    def __init__(self, root: str | None = None):
        self.root = Path(root or os.environ.get("LOCAL_STATE_DIR", ".state")); self.root.mkdir(parents=True, exist_ok=True)

    def put(self, pid: str, doc: dict):
        expected, new = _next_version(doc)
        p = self.root / f"{pid}.json"
        current = json.loads(p.read_text()).get("version", 0) if p.exists() else 0
        if current != expected:
            raise ConflictError(pid)
        doc["version"] = new
        p.write_text(json.dumps(doc, default=str))

    def get(self, pid: str) -> dict | None:
        p = self.root / f"{pid}.json"
        if not p.exists():
            return None
        doc = json.loads(p.read_text())
        if doc.get("expires_at") and doc["expires_at"] < time.time():
            self.delete(pid)
            return None
        return doc

    def delete(self, pid: str):
        (self.root / f"{pid}.json").unlink(missing_ok=True)

class DynamoStore:
    def __init__(self):
        import boto3
        self.table = boto3.resource("dynamodb").Table(os.environ["TABLE_NAME"])

    def put(self, pid: str, doc: dict):
        expected, new = _next_version(doc)
        doc["version"] = new
        item = {"pk": f"PROJECT#{pid}", "sk": "STATE", "version": new, "doc": json.dumps(doc, default=str)}
        if doc.get("expires_at"):
            item["ttl"] = int(doc["expires_at"])          # DynamoDB TTL attribute (see template.yaml)
        try:
            if expected == 0:                             # new project, or one saved before versions existed
                self.table.put_item(Item=item, ConditionExpression="attribute_not_exists(pk) OR attribute_not_exists(version)")
            else:
                self.table.put_item(Item=item, ConditionExpression="version = :v", ExpressionAttributeValues={":v": expected})
        except self.table.meta.client.exceptions.ConditionalCheckFailedException:
            doc["version"] = expected
            raise ConflictError(pid)

    def get(self, pid: str) -> dict | None:
        r = self.table.get_item(Key={"pk": f"PROJECT#{pid}", "sk": "STATE"}, ConsistentRead=True).get("Item")
        if not r:
            return None
        doc = json.loads(r["doc"])
        return None if doc.get("expires_at") and doc["expires_at"] < time.time() else doc

    def delete(self, pid: str):
        self.table.delete_item(Key={"pk": f"PROJECT#{pid}", "sk": "STATE"})

def get_store():
    return DynamoStore() if os.environ.get("STATE_BACKEND") == "dynamodb" else LocalStore()

def new_id() -> str:
    return uuid.uuid4().hex[:10]

"""Project state. Local JSON files for development, DynamoDB when running on AWS (STATE_BACKEND=dynamodb).
Every project carries an expiry; expired projects read as missing and are cleaned up (DynamoDB TTL on AWS)."""
import json, os, time, uuid
from pathlib import Path

class LocalStore:
    def __init__(self, root: str | None = None):
        self.root = Path(root or os.environ.get("LOCAL_STATE_DIR", ".state")); self.root.mkdir(parents=True, exist_ok=True)

    def put(self, pid: str, doc: dict):
        (self.root / f"{pid}.json").write_text(json.dumps(doc, default=str))

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
        item = {"pk": f"PROJECT#{pid}", "sk": "STATE", "doc": json.dumps(doc, default=str)}
        if doc.get("expires_at"):
            item["ttl"] = int(doc["expires_at"])          # DynamoDB TTL attribute (see template.yaml)
        self.table.put_item(Item=item)

    def get(self, pid: str) -> dict | None:
        r = self.table.get_item(Key={"pk": f"PROJECT#{pid}", "sk": "STATE"}).get("Item")
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

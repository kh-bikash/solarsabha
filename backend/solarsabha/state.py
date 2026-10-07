"""Project state. Local JSON files for development, DynamoDB when running on AWS (STATE_BACKEND=dynamodb)."""
import json, os, uuid
from pathlib import Path

class LocalStore:
    def __init__(self, root: str | None = None):
        self.root = Path(root or os.environ.get("LOCAL_STATE_DIR", ".state")); self.root.mkdir(parents=True, exist_ok=True)
    def put(self, pid: str, doc: dict): (self.root / f"{pid}.json").write_text(json.dumps(doc, default=str))
    def get(self, pid: str) -> dict | None:
        p = self.root / f"{pid}.json"; return json.loads(p.read_text()) if p.exists() else None

class DynamoStore:
    def __init__(self):
        import boto3
        self.table = boto3.resource("dynamodb").Table(os.environ["TABLE_NAME"])
    def put(self, pid: str, doc: dict):
        self.table.put_item(Item={"pk": f"PROJECT#{pid}", "sk": "STATE", "doc": json.dumps(doc, default=str)})
    def get(self, pid: str) -> dict | None:
        r = self.table.get_item(Key={"pk": f"PROJECT#{pid}", "sk": "STATE"}).get("Item")
        return json.loads(r["doc"]) if r else None

def get_store():
    return DynamoStore() if os.environ.get("STATE_BACKEND") == "dynamodb" else LocalStore()

def new_id() -> str:
    return uuid.uuid4().hex[:10]

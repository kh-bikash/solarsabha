"""Write frontend/src/mock/demo.json so the UI works with no backend (static demo mode).
Three snapshots of the sample project, built by the same code the API uses. Re-run after changing the pipeline."""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from solarsabha import project as P
from solarsabha.pipeline import load_sample_inputs
from solarsabha.schemas import CreateProject

def snapshot(doc):
    return json.loads(json.dumps(P.public(doc), default=str))

doc, _ = P.create("demo000000", CreateProject(sample=True))
frames = {"start": snapshot(doc)}
doc["sim_offset_days"] = 40
frames["day50"] = snapshot(P.recompute(doc))
doc["discom_reply"] = load_sample_inputs()["discom_reply_example"]
frames["day50_reply"] = snapshot(P.recompute(doc))
(ROOT / "frontend/src/mock/demo.json").write_text(json.dumps(frames, indent=1, default=str), encoding="utf-8")
print("wrote frontend/src/mock/demo.json")

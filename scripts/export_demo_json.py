"""Write frontend/src/mock/demo.json so the UI works with no backend. Re-run after changing the pipeline."""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from solarsabha.pipeline import run_offline, load_sample_inputs
i = load_sample_inputs()
frames = {"day0": run_offline(i, 0), "day50": run_offline(i, 50), "day50_reply": run_offline(i, 50, discom_reply=i["discom_reply_example"])}
(ROOT / "frontend/src/mock/demo.json").write_text(json.dumps(frames, indent=1, default=str))
print("wrote frontend/src/mock/demo.json")

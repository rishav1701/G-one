"""Package the public ICU research candidate outside the active model registry."""
import hashlib, json, shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/".tools"/"physionet-challenge-2019"/"candidate"
DEST=ROOT/"models"/"research"/"physionet-challenge-2019-sepsis"
if not (SOURCE/"manifest.json").is_file(): raise SystemExit("Train the research candidate first.")
manifest=json.loads((SOURCE/"manifest.json").read_text(encoding="utf-8"))
metrics=json.loads((SOURCE/"metrics.json").read_text(encoding="utf-8"))
if manifest.get("acceptance_passed") is not False or manifest.get("active") is not False:
    raise SystemExit("Refusing to package an artifact marked accepted or active.")
if metrics.get("status") != "research_candidate_not_clinically_validated":
    raise SystemExit("Refusing to package metrics without the research-only status.")
DEST.mkdir(parents=True,exist_ok=True)
for name in ("model.joblib","manifest.json","metrics.json"):
    shutil.copy2(SOURCE/name,DEST/name)
shutil.copy2(SOURCE.parent/"LICENSE.txt",DEST/"LICENSE.txt")
shutil.copy2(SOURCE/"model_card.md",DEST/"model_card.md")
copy_manifest=json.loads((DEST/"manifest.json").read_text(encoding="utf-8"))
if hashlib.sha256((DEST/"model.joblib").read_bytes()).hexdigest()!=copy_manifest["model_sha256"]:
    raise SystemExit("Model checksum mismatch after packaging.")
if hashlib.sha256((DEST/"metrics.json").read_bytes()).hexdigest()!=copy_manifest["metrics_sha256"]:
    raise SystemExit("Metrics checksum mismatch after packaging.")
print(f"Packaged inactive research artifact: {DEST}")

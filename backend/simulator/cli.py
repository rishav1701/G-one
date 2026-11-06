import argparse
import json

from app.core.config import settings
from app.core.db import SessionLocal
from simulator.engine import reset_simulation, run_seed


def main():
    parser = argparse.ArgumentParser(description="Reset and reseed the G One simulated demonstration data.")
    parser.add_argument("command", choices=("reset", "reset-seed"))
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    if settings.environment != "development":
        raise SystemExit("The simulator is available only in development.")
    db = SessionLocal()
    try:
        if args.command == "reset":
            reset_simulation(db)
            print(json.dumps({"status": "reset"}, separators=(",", ":")))
        else:
            result = run_seed(db, args.seed)
            print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    finally:
        db.close()


if __name__ == "__main__":
    main()

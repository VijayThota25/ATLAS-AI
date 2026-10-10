
import json
from pathlib import Path


DATA_DIR = Path(__file__).resolve().parent / "data"
INCIDENTS_FILE = DATA_DIR / "incidents.jsonl"


def save_incident(incident):
    """Append a synthetic incident to local storage."""

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    with INCIDENTS_FILE.open("a", encoding="utf-8") as file:
        file.write(json.dumps(incident) + "\n")

    return str(INCIDENTS_FILE)


if __name__ == "__main__":
    sample_incident = {
        "incident_id": "TEST-001",
        "incident_type": "STORAGE_TEST",
        "severity": "LOW",
        "environment": "SIMULATION"
    }

    path = save_incident(sample_incident)

    print("ATLAS STORAGE ENGINE")
    print("--------------------")
    print("Incident saved successfully!")
    print("File:", path)

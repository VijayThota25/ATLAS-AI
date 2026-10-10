"""Read saved ATLAS synthetic incident reports without changing them."""
import json
from storage import INCIDENTS_FILE


def show_history():
    if not INCIDENTS_FILE.exists():
        print("No saved incidents yet. Run python main.py first.")
        return

    print("ATLAS AI | SAVED INCIDENT HISTORY")
    count = 0
    with INCIDENTS_FILE.open("r", encoding="utf-8") as records:
        for line_number, line in enumerate(records, 1):
            if not line.strip():
                continue
            try:
                incident = json.loads(line)
            except json.JSONDecodeError:
                print(f"Skipping invalid record on line {line_number}")
                continue
            count += 1
            print(f"{count}. {incident.get('incident_type', 'UNKNOWN')} | "
                  f"{incident.get('severity', 'UNKNOWN')} | "
                  f"{incident.get('status', 'UNKNOWN')} | "
                  f"{incident.get('incident_id', 'NO-ID')}")
    print(f"Total saved records: {count}")


if __name__ == "__main__":
    show_history()

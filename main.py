from datetime import datetime, timezone
from uuid import uuid4
import json
from detector import detect_incident
from scenarios import generate_scenario



from storage import save_incident

def generate_incident():
    """Create a fictional payment-processing incident."""

    scenario = generate_scenario()
    metrics = scenario["metrics"]

    incident = {

        "incident_id": str(uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "system": "ATLAS Payment Gateway",
        "incident_type": scenario["scenario"].upper(),
        "severity": "HIGH",
        "provider": "SyntheticPay",
        "metrics": metrics,
        "status": "DETECTED",
        "environment": "SIMULATION"
    }

    return incident


def main():
    print("=" * 55)
    print("ATLAS AI")
    print("Autonomous Trust, Learning & Action Simulation Engine")
    print("=" * 55)

    incident = generate_incident()
    
    detection = detect_incident(incident["metrics"])
    incident["severity"] = detection["severity"]
    incident["detection_reasons"] = detection["reasons"]
    incident["status"] = "DETECTED" if detection["incident_detected"] else "HEALTHY"



    print(f'\nATLAS SYSTEM STATUS: {incident["status"]}\n')
    print(json.dumps(incident, indent=4))
    save_incident(incident)

    print("\nATLAS Incident Simulator: Running successfully!")


if __name__ == "__main__":
    main()

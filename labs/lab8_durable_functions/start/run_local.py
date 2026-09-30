"""Start, approve and save a locally running Durable Functions review."""

import json
import time
from pathlib import Path
from urllib.request import Request, urlopen

BASE = "http://localhost:7071/api"
ROOT = Path(__file__).resolve().parents[3]


def request_json(url: str, payload: dict | None = None) -> dict:
    data = None if payload is None else json.dumps(payload).encode()
    request = Request(url, data=data, headers={"Content-Type": "application/json"})
    with urlopen(request, timeout=10) as response:  # local workshop endpoint
        return json.loads(response.read()) if response.length != 0 else {}


def main() -> None:
    started = request_json(f"{BASE}/reviews", {})
    instance_id = started["id"]
    print(f"Started {instance_id}; restart func while it waits if you want to test recovery.")
    request_json(f"{BASE}/reviews/{instance_id}/approval", {"decision": "approve"})
    for _ in range(60):
        status = request_json(started["statusQueryGetUri"])
        if status["runtimeStatus"] in {"Completed", "Failed", "Terminated"}:
            break
        time.sleep(1)
    else:
        raise TimeoutError("Durable review did not finish in 60 seconds")
    if status["runtimeStatus"] != "Completed":
        raise RuntimeError(f"Durable review ended as {status['runtimeStatus']}")
    record = status["output"]["record"]
    output = ROOT / "out" / "lab8_durable.json"
    wrapped = {"technique": "8. Azure Durable Functions", "runtime_s": 0, "record": record}
    output.write_text(json.dumps(wrapped, indent=2), encoding="utf-8")
    print(f"Saved {output.relative_to(ROOT)}")


if __name__ == "__main__":
    main()

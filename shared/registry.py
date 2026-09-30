"""Safe client for the Lab 5 mock vendor-registry REST API."""

import json
import os
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen

from pydantic import BaseModel, ConfigDict

MAX_RESPONSE_BYTES = 16_384


class RegistryRecord(BaseModel):
    model_config = ConfigDict(extra="ignore")

    registration_number: str
    legal_name: str
    status: str
    country: str


def _safe_base_url(value: str) -> str:
    parsed = urlparse(value)
    local = parsed.hostname in {"127.0.0.1", "localhost", "::1"}
    if parsed.scheme not in ({"http", "https"} if local else {"https"}) or not parsed.netloc:
        raise ValueError("Registry URL must be HTTPS, except for the local workshop service")
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError("Registry URL must not contain credentials, query parameters or fragments")
    return value.rstrip("/")


def lookup_vendor(registration_number: str, *, base_url: str | None = None,
                  token: str | None = None, timeout: float = 3.0) -> RegistryRecord:
    if not registration_number or len(registration_number) > 40:
        raise ValueError("Invalid registration number")
    base = _safe_base_url(base_url or os.getenv("REGISTRY_BASE_URL", "http://127.0.0.1:8765"))
    secret = token or os.getenv("REGISTRY_TOKEN", "")
    if not secret:
        raise RuntimeError("REGISTRY_TOKEN is missing")
    request = Request(f"{base}/vendors/{quote(registration_number, safe='')}",
                      headers={"Authorization": f"Bearer {secret}", "Accept": "application/json"})
    try:
        with urlopen(request, timeout=timeout) as response:
            raw = response.read(MAX_RESPONSE_BYTES + 1)
    except HTTPError as exc:
        raise RuntimeError(f"Registry returned HTTP {exc.code}") from None
    except (TimeoutError, URLError) as exc:
        raise RuntimeError("Registry request failed or timed out") from exc
    if len(raw) > MAX_RESPONSE_BYTES:
        raise RuntimeError("Registry response exceeded the size limit")
    try:
        return RegistryRecord.model_validate(json.loads(raw))
    except (ValueError, json.JSONDecodeError) as exc:
        raise RuntimeError("Registry returned an invalid response") from exc

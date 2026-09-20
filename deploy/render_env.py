"""Create a private Compose raw env file from an Azure secret, without logging values."""
import json
import os
import re
import sys
from pathlib import Path

REQUIRED = ("DATABASE_URL", "REDIS_URL", "QDRANT_URL", "SECRET_KEY", "FRONTEND_URL", "DATABASE_SSL")

def render(raw):
    try:
        config = json.loads(raw)
    except (ValueError, TypeError):
        raise ValueError("PRODUCTION_ENV_JSON must be a JSON object") from None
    if not isinstance(config, dict):
        raise ValueError("PRODUCTION_ENV_JSON must be a JSON object")
    for key in REQUIRED:
        if not str(config.get(key, "")).strip():
            raise ValueError(f"Missing required setting: {key}")
    config.setdefault("CELERY_BROKER_URL", config["REDIS_URL"])
    config.setdefault("CELERY_RESULT_BACKEND", config["REDIS_URL"])
    config.setdefault("DEBUG", False)
    provider = config.setdefault("LLM_PROVIDER", "groq")
    needed = "GROQ_API_KEY" if provider == "groq" else "OLLAMA_BASE_URL"
    if provider not in ("groq", "ollama") or not config.get(needed):
        raise ValueError("Set LLM_PROVIDER and its required API key or endpoint")
    if str(config["DATABASE_SSL"]).lower() not in ("true", "false"):
        raise ValueError("DATABASE_SSL must be true or false")
    result = []
    for key, value in config.items():
        if not re.fullmatch(r"[A-Z][A-Z0-9_]*", key):
            raise ValueError("Environment setting names must be uppercase identifiers")
        if not isinstance(value, (str, int, float, bool)):
            raise ValueError(f"Setting {key} must be a scalar value")
        value = str(value).lower() if isinstance(value, bool) else str(value)
        if any(char in value for char in ("\r", "\n", "\0")):
            raise ValueError(f"Setting {key} must be a single line without NUL")
        result.append(f"{key}={value}")
    return "\n".join(result) + "\n"

def main():
    target = Path(sys.argv[1])
    # Validate everything before creating a file. O_EXCL prevents overwriting another file.
    text = render(os.environ.get("PRODUCTION_ENV_JSON", ""))
    descriptor = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as output:
        output.write(text)

if __name__ == "__main__":
    try:
        main()
    except ValueError as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)

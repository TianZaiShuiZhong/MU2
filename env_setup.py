import os
from pathlib import Path


def load_environment() -> None:
    """Load environment variables from a local .env file when available."""
    env_path = Path(__file__).with_name(".env")
    if not env_path.exists():
        return

    try:
        from dotenv import load_dotenv
    except ImportError:
        for raw_line in env_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value
        return

    load_dotenv(env_path)

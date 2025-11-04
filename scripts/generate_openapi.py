"""Generate OpenAPI schema file."""

from __future__ import annotations

import json
from pathlib import Path

from caresense.api.main import app
from fastapi.openapi.utils import get_openapi


def main() -> None:
    schema = get_openapi(
        title=app.title,
        version=app.version,
        routes=app.routes,
    )
    output = Path("docs") / "openapi.generated.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(schema, indent=2))
    print(f"Generated {output}")


if __name__ == "__main__":
    main()

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from app.main import create_v2_app


def export_openapi(output_path: str | Path) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    app = create_v2_app()
    path.write_text(
        json.dumps(app.openapi(), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Export the FastAPI OpenAPI schema.")
    parser.add_argument("output", type=Path, help="Destination JSON file path.")
    args = parser.parse_args(argv)
    export_openapi(args.output)


if __name__ == "__main__":
    main()

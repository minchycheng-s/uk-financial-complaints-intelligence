"""Execute the trusted profiling notebook using existing project dependencies."""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import os
import traceback
from pathlib import Path
from typing import Any

import pandas as pd


def execute_notebook(path: Path, max_display_rows: int = 30) -> None:
    """Execute code cells in order and store bounded, standard notebook outputs."""
    notebook = json.loads(path.read_text(encoding="utf-8"))
    namespace: dict[str, Any] = {"__name__": "__notebook__"}
    execution_count = 0
    original_directory = Path.cwd()
    os.chdir(path.parent)
    try:
        for cell in notebook.get("cells", []):
            if cell.get("cell_type") != "code":
                continue
            execution_count += 1
            outputs: list[dict[str, Any]] = []

            def display(*objects: Any) -> None:
                for value in objects:
                    displayed = value
                    suffix = ""
                    if isinstance(value, pd.DataFrame) and len(value) > max_display_rows:
                        displayed = value.head(max_display_rows)
                        suffix = f"\n[Preview limited to {max_display_rows} of {len(value)} rows]"
                    data = {"text/plain": repr(displayed) + suffix}
                    if hasattr(displayed, "_repr_html_"):
                        html = displayed._repr_html_()
                        if html:
                            data["text/html"] = html + (f"<p>{suffix.strip()}</p>" if suffix else "")
                    outputs.append({"output_type": "display_data", "metadata": {}, "data": data})

            namespace["display"] = display
            stream = io.StringIO()
            try:
                with contextlib.redirect_stdout(stream), contextlib.redirect_stderr(stream):
                    exec(compile("".join(cell.get("source", [])), str(path), "exec"), namespace)
                if stream.getvalue():
                    outputs.insert(0, {"output_type": "stream", "name": "stdout",
                                       "text": stream.getvalue().splitlines(keepends=True)})
            except Exception as exc:
                outputs.append({
                    "output_type": "error", "ename": type(exc).__name__, "evalue": str(exc),
                    "traceback": traceback.format_exc().splitlines(),
                })
                cell["execution_count"] = execution_count
                cell["outputs"] = outputs
                raise
            cell["execution_count"] = execution_count
            cell["outputs"] = outputs
    finally:
        os.chdir(original_directory)
        path.write_text(json.dumps(notebook, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("notebook", type=Path, nargs="?",
                        default=Path("notebooks/01_workbook_profiling.ipynb"))
    parser.add_argument("--max-display-rows", type=int, default=30)
    args = parser.parse_args(argv)
    execute_notebook(args.notebook.resolve(), args.max_display_rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

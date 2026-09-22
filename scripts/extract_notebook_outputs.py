"""Extract saved notebook outputs without executing any notebook cells."""

from __future__ import annotations

import base64
import html
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
NOTEBOOK = ROOT / "catfish_multitask_colab.ipynb"
DESTINATION = ROOT / "chapter_4_5_materials"


def as_text(value: object) -> str:
    if isinstance(value, list):
        return "".join(str(part) for part in value)
    return str(value)


def main() -> None:
    notebook = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    DESTINATION.mkdir(exist_ok=True)
    images = DESTINATION / "images"
    tables = DESTINATION / "tables"
    text_outputs = DESTINATION / "text_outputs"
    raw_outputs = DESTINATION / "raw_outputs"
    for directory in (images, tables, text_outputs, raw_outputs):
        directory.mkdir(exist_ok=True)

    manifest: list[dict[str, object]] = []
    report_parts = [
        "<!doctype html><html><head><meta charset='utf-8'>",
        "<title>Catfish notebook saved results</title>",
        "<style>body{max-width:1100px;margin:2rem auto;padding:0 1rem;font:16px/1.55 system-ui;color:#172b36}"
        "pre{white-space:pre-wrap;background:#f4f7f8;padding:1rem;border-radius:8px;overflow:auto}"
        "img{max-width:100%;height:auto;border:1px solid #ddd}table{border-collapse:collapse;display:block;overflow:auto}"
        "th,td{border:1px solid #ccc;padding:.4rem}.cell{border-top:2px solid #dce7ea;padding-top:1rem;margin-top:2rem}"
        ".output{margin:1rem 0;padding-left:1rem;border-left:4px solid #5aa}</style></head><body>",
        "<h1>Catfish multi-task notebook — saved results</h1>",
        "<p>This static report was extracted from the notebook without executing any cells.</p>",
    ]

    image_number = table_number = text_number = raw_number = 0
    for cell_index, cell in enumerate(notebook.get("cells", [])):
        source = as_text(cell.get("source", ""))
        report_parts.append(f"<section class='cell'><h2>Cell {cell_index} — {html.escape(cell.get('cell_type', 'unknown'))}</h2>")
        if cell.get("cell_type") == "markdown":
            report_parts.append(f"<pre>{html.escape(source)}</pre>")
        else:
            report_parts.append(f"<details><summary>Code</summary><pre>{html.escape(source)}</pre></details>")

        for output_index, output in enumerate(cell.get("outputs", [])):
            entry: dict[str, object] = {
                "cell": cell_index,
                "output": output_index,
                "output_type": output.get("output_type"),
                "files": [],
            }
            report_parts.append("<div class='output'>")
            stream_text = as_text(output.get("text", ""))
            if stream_text:
                text_number += 1
                name = f"cell_{cell_index:02d}_output_{output_index:02d}_{text_number:02d}.txt"
                (text_outputs / name).write_text(stream_text, encoding="utf-8")
                entry["files"].append(f"text_outputs/{name}")
                report_parts.append(f"<pre>{html.escape(stream_text)}</pre>")

            data = output.get("data", {})
            if "image/png" in data:
                image_number += 1
                name = f"cell_{cell_index:02d}_image_{image_number:02d}.png"
                (images / name).write_bytes(base64.b64decode(as_text(data["image/png"])))
                entry["files"].append(f"images/{name}")
                report_parts.append(f"<img src='images/{name}' alt='Notebook output from cell {cell_index}'>")
            if "text/html" in data:
                table_number += 1
                name = f"cell_{cell_index:02d}_table_{table_number:02d}.html"
                rendered = as_text(data["text/html"])
                (tables / name).write_text(rendered, encoding="utf-8")
                entry["files"].append(f"tables/{name}")
                report_parts.append(rendered)
            elif "text/plain" in data and "image/png" not in data:
                plain = as_text(data["text/plain"])
                text_number += 1
                name = f"cell_{cell_index:02d}_output_{output_index:02d}_{text_number:02d}.txt"
                (text_outputs / name).write_text(plain, encoding="utf-8")
                entry["files"].append(f"text_outputs/{name}")
                report_parts.append(f"<pre>{html.escape(plain)}</pre>")

            for mime, value in data.items():
                if mime in {"image/png", "text/html", "text/plain"}:
                    continue
                raw_number += 1
                name = f"cell_{cell_index:02d}_output_{output_index:02d}_{raw_number:02d}.json"
                (raw_outputs / name).write_text(
                    json.dumps({"mime_type": mime, "value": value}, indent=2), encoding="utf-8"
                )
                entry["files"].append(f"raw_outputs/{name}")
            report_parts.append("</div>")
            manifest.append(entry)
        report_parts.append("</section>")

    report_parts.append("</body></html>")
    (DESTINATION / "notebook_results.html").write_text("\n".join(report_parts), encoding="utf-8")
    (DESTINATION / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    readme = f"""# Chapter 4 and 5 source materials

These files were extracted from `catfish_multitask_colab.ipynb` without running any notebook cells.

- Open `notebook_results.html` for the complete browsable record.
- `images/` contains {image_number} embedded PNG figures.
- `tables/` contains {table_number} saved HTML tables.
- `text_outputs/` contains {text_number} console and plain-text results.
- `raw_outputs/` preserves {raw_number} Colab/JavaScript output payloads.
- `manifest.json` maps every extracted file to its original cell and output.

The original notebook remains the authoritative source. Keep it alongside this folder.
"""
    (DESTINATION / "README.md").write_text(readme, encoding="utf-8")
    print(f"Extracted {image_number} images, {table_number} tables, {text_number} text outputs, and {raw_number} raw outputs.")


if __name__ == "__main__":
    main()

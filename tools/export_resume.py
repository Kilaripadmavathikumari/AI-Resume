from __future__ import annotations

from datetime import datetime
from pathlib import Path


def export_markdown_resume(markdown_content: str) -> str:
    output_dir = Path("outputs")
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = output_dir / f"resume_{timestamp}.md"
    file_path.write_text(markdown_content, encoding="utf-8")

    return str(file_path.resolve())

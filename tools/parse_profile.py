from __future__ import annotations


def parse_profile_input(raw_text: str) -> str:
    cleaned_lines: list[str] = []

    for line in raw_text.splitlines():
        normalized = " ".join(line.strip().split())
        if normalized:
            cleaned_lines.append(normalized)

    return "\n".join(cleaned_lines).strip()

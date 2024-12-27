"""Inevitable hodge-podge of odds and ends functions"""

def brief_version(value: str, max_length: int = 250) -> str:
    summary = value.replace("\n", "\\n")
    if len(summary) > max_length:
        summary = summary[:50] + "…"
    return summary

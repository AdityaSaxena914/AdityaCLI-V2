from pathlib import Path
from functools import lru_cache

PROMPTS_DIR = Path(__file__).parent


@lru_cache(maxsize=8)
def load_prompt(name: str) -> str:
    return (
        PROMPTS_DIR / f"{name}.txt"
    ).read_text(encoding="utf-8")

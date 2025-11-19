from functools import lru_cache
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import logging

LOGGER = logging.getLogger(__name__)

DEFAULT_KB_PATH = Path(__file__).resolve().parents[1] / "data" / "knowledge_base.json"

@lru_cache(maxsize=1)
def load_kb(path: Optional[Union[str, Path]] = None) -> List[Dict[str, Any]]:
    kb_path = Path(path) if path else DEFAULT_KB_PATH
    if not kb_path.exists():
        raise FileNotFoundError(f"Knowledge base not found at {kb_path}")
    with kb_path.open("r", encoding="utf-8") as source:
        data = json.load(source)
    LOGGER.info(f"Loaded {len(data)} KB entries from {kb_path}")
    return data

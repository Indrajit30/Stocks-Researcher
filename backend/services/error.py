# backend/services/errors.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, Optional

@dataclass
class StepError:
    step: str
    error_type: str
    message: str

    def to_dict(self) -> Dict[str, Any]:
        return {"step": self.step, "error_type": self.error_type, "message": self.message}

def safe_step(step: str, fn, errors: list, default: Any = None) -> Any:
    try:
        return fn()
    except Exception as e:
        errors.append(StepError(step=step, error_type=type(e).__name__, message=str(e)).to_dict())
        return default
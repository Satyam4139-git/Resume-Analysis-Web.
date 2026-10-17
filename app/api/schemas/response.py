from pydantic import BaseModel
from typing import Any


class AnalysisResponse(BaseModel):
    result: Any
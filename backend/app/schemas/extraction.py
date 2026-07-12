from pydantic import BaseModel


class ExtractionResult(BaseModel):
    success: bool

    text: str

    page_count: int = 0

    word_count: int = 0

    character_count: int = 0

    used_ocr: bool = False

    metadata: dict = {}

    error: str | None = None
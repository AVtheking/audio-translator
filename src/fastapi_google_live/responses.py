from pydantic import BaseModel, Field


class TranslationResponse(BaseModel):
    translation: str = Field(..., description="The translated text")
    target_language: str = Field(..., description="The target language code")


class ErrorResponse(BaseModel):
    message: str = Field(..., description="The error message")

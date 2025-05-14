from pydantic import BaseModel, Field, field_validator
from fastapi_google_live.supported_languages import SUPPORTED_LANGUAGES


class TranslationRequest(BaseModel):
    target_language: str = Field(
        ..., description="The target language code for translation"
    )

    @property
    def target_language_name(self) -> str:
        return SUPPORTED_LANGUAGES[self.target_language]

    @field_validator("target_language")
    def validate_target_language(cls, v):
        if v not in SUPPORTED_LANGUAGES:
            lang_list = ", ".join(SUPPORTED_LANGUAGES.keys())
            raise ValueError(
                f"Invalid target language: {v}. Supported languages: {lang_list}"
            )
        return v

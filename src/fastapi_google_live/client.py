from typing import Annotated
from fastapi_google_live.settings import Settings, get_settings
from google import genai
from fastapi import Depends, HTTPException


def get_gemini_client(settings: Settings = Depends(get_settings)):
    if not settings.GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY is not set")
    return genai.Client(api_key=settings.GEMINI_API_KEY)

from fastapi import (
    FastAPI,
    status,
    BackgroundTasks,
    Depends,
    File,
    UploadFile,
    Form,
    HTTPException,
)
from dotenv import load_dotenv
from google import genai
from google.genai import types
from fastapi.responses import JSONResponse
from fastapi_google_live.request import TranslationRequest
from fastapi_google_live.responses import ErrorResponse, TranslationResponse
from fastapi_google_live.supported_languages import SUPPORTED_LANGUAGES
from fastapi_google_live.client import get_gemini_client
from fastapi_google_live.settings import get_settings, Settings
from fastapi_google_live.cleanup import cleanup_files
from fastapi_google_live.translation import (
    convert_to_pcm,
    get_translation,
    format_language_list,
)
from pathlib import Path
import tempfile
import logging

load_dotenv()


app = FastAPI(
    title="Audio Translation API",
    description="API for translating audio files using Google Gemini.",
)

logger = logging.getLogger("uvicorn.error")


@app.get("/")
def read_root():
    return {"message": "Hello World"}


description = f"""
Translate an audio file to the specified target language.

**Supported Languages**:

{format_language_list()}

"""


@app.post(
    "/translate",
    summary="Translate audio to a target language",
    description=description,
    response_model=TranslationResponse,
    responses={
        status.HTTP_200_OK: {"model": TranslationResponse},
        status.HTTP_400_BAD_REQUEST: {"model": ErrorResponse},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": ErrorResponse},
    },
)
async def translate(
    background_tasks: BackgroundTasks,
    audio_file: UploadFile = File(...),
    target_language: str = Form(...),
    client: genai.Client = Depends(get_gemini_client),
    settings: Settings = Depends(get_settings),
):
    try:
        input_path: str | None = None
        output_pcm_path: str | None = None

        translation_request = TranslationRequest(target_language=target_language)

        if not audio_file.filename or not any(
            audio_file.filename.endswith(f".{ext}")
            for ext in settings.SUPPORTED_AUDIO_FORMATS
        ):
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=ErrorResponse(message="Unsupported file format").model_dump(),
            )

        suffix = Path(audio_file.filename).suffix

        with tempfile.NamedTemporaryFile(
            delete=False, suffix=suffix
        ) as temp_audio_file:
            temp_audio_file.write(await audio_file.read())
            input_path = temp_audio_file.name

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pcm") as tmp_out:
            output_pcm_path = tmp_out.name

        logger.info(f"Converting audio to PCM: {output_pcm_path}")
        await convert_to_pcm(input_path, output_pcm_path, settings.PCM_SAMPLE_RATE)
        logger.info(f"Converted audio to PCM: {output_pcm_path}")

        audio_bytes = Path(output_pcm_path).read_bytes()

        system_instruction = types.Content(
            parts=[
                types.Part(
                    text=f"You are a helpful assistant.Translate the audio to {target_language}."
                )
            ]
        )

        translation = await get_translation(
            client,
            settings.GEMINI_MODEL,
            settings.GEMINI_CONFIG,
            audio_bytes,
            system_instruction,
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=TranslationResponse(
                translation=translation.strip(),
                target_language=translation_request.target_language_name,
            ).model_dump(),
        )
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Error translating audio: {e}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=ErrorResponse(message=str(e)).model_dump(),
        )
    except Exception as e:
        logger.error(f"Error translating audio: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse(message=str(e)).model_dump(),
        )

    finally:
        background_tasks.add_task(cleanup_files, input_path, output_pcm_path)

from fastapi import FastAPI
from dotenv import load_dotenv
from google import genai
from google.genai import types
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import JSONResponse
from pathlib import Path

import os
import ffmpeg
import tempfile

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=GEMINI_API_KEY)
model = "gemini-2.0-flash-live-001"

CONFIG = {"response_modalities": ["TEXT"]}

app = FastAPI()


def convert_to_pcm(input_path: str, output_path: str):
    ffmpeg.input(input_path).output(
        output_path, format="s16le", acodec="pcm_s16le", ac=1, ar="16000"
    ).overwrite_output().run()


async def get_translation(audio_bytes: bytes, system_instruction: types.Content):
    translation = ""
    async with client.aio.live.connect(
        model=model,
        config={
            **CONFIG,
            "system_instruction": system_instruction,
        },
    ) as session:

        await session.send_realtime_input(
            media=types.Blob(data=audio_bytes, mime_type="audio/pcm;rate=16000")
        )
        await session.send_realtime_input(audio_stream_end=True)

        async for msg in session.receive():
            if msg.text is not None:
                translation += msg.text

    return translation


@app.get("/")
def read_root():
    return {"message": "Hello World"}


@app.post("/translate")
async def translate(
    audio_file: UploadFile = File(...), target_language: str = Form(...)
):
    try:
        if not audio_file.filename.endswith((".mp3", ".wav", ".m4a", ".ogg")):
            return JSONResponse(
                status_code=400,
                content={"message": "Unsupported file format"},
            )

        suffix = Path(audio_file.filename).suffix
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=suffix
        ) as temp_audio_file:
            temp_audio_file.write(await audio_file.read())
            input_path = temp_audio_file.name

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pcm") as tmp_out:
            output_pcm_path = tmp_out.name

        convert_to_pcm(input_path, output_pcm_path)
        audio_bytes = Path(output_pcm_path).read_bytes()

        system_instruction = types.Content(
            parts=[
                types.Part(
                    text=f"You are a helpful assistant.Translate the audio to {target_language}."
                )
            ]
        )

        translation = await get_translation(audio_bytes, system_instruction)

        return JSONResponse(
            status_code=200,
            content={
                "translation": translation.strip(),
                "target_language": target_language,
            },
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"message": str(e)},
        )

    finally:
        if os.path.exists(input_path):
            os.remove(input_path)
        if os.path.exists(output_pcm_path):
            os.remove(output_pcm_path)

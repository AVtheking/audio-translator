import ffmpeg
import asyncio
import logging
from google.genai import types
from fastapi_google_live.supported_languages import SUPPORTED_LANGUAGES

logger = logging.getLogger(__name__)


def format_language_list():
    return "\n".join(
        [f"- {code}: {name}" for code, name in SUPPORTED_LANGUAGES.items()]
    )


async def convert_to_pcm(input_path: str, output_path: str, sample_rate: int = 16000):
    logger.info(f"Converting audio to PCM: {output_path}")
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(
        None,
        lambda: ffmpeg.input(input_path)
        .output(
            output_path, format="s16le", acodec="pcm_s16le", ac=1, ar=f"{sample_rate}"
        )
        .overwrite_output()
        .run(),
    )

    logger.info(f"Converted audio to PCM: {output_path}")


async def get_translation(
    client, model, config, audio_bytes: bytes, system_instruction: types.Content
):
    logger.info("Getting translation")
    translation = ""
    async with client.aio.live.connect(
        model=model,
        config={
            **config,
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
                logger.info(f"Translation: {translation}")
    return translation

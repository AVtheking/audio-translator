from fastapi import FastAPI
from dotenv import load_dotenv
from google import genai
from fastapi import FastAPI, File, UploadFile

import os

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=GEMINI_API_KEY)
model = "gemini-2.0-flash-live-001"

config = {"response_modalities": ["TEXT"]}

app = FastAPI()


@app.get("/")
def read_root():
    return {"message": "Hello World"}


@app.post("/translate")
async def translate(file: UploadFile, target_language: str):
    return {"filename": file.filename}

from openai import OpenAI
from fastapi import UploadFile
import os
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

def process_voice(audio: UploadFile):
    transcript = client.audio.transcriptions.create(
        model = "gpt-4o-transcribe",
        file = audio.file,
    )

    completion = client.response.parse(
        model = "gpt-4.1",
        input = transcript.text,
        text_format = "text",
    )

    return completion.output_parsed
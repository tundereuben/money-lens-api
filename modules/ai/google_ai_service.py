import json
import time
from dotenv import load_dotenv
from fastapi import logger, HTTPException
from google import genai
from google.genai import types
from google.genai.errors import ClientError
import os
from datetime import datetime

from tenacity import retry, stop_after_attempt, wait_fixed

from schemas.expense import ExpenseCreate

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def extract_transaction(audio_path: str, categories: list[dict[str, object]]):
    timeout = 60  # seconds
    start = time.time()
    
    uploaded = client.files.upload(
        file=audio_path,  
        config={
        "mime_type": "audio/webm"
    })

    while True:
        uploaded_file = client.files.get(name=uploaded.name)
        if uploaded_file.state.name == "ACTIVE":
            break

        if uploaded_file.state.name == "FAILED":
            print(uploaded_file)
            raise RuntimeError("File processing failed")
                
        if time.time() - start > timeout:
            raise TimeoutError("File processing timed out")
        
        time.sleep(2)  # Wait for a second before checking again

    
    prompt_template = """
    You are an intelligent financial assistant.
    Your goal is to extract one or more expenses from spoken language.

    CURRENT DATETIME CONTEXT:
    - Today's Date: {{CURRENT_DATE}} (Format: YYYY-MM-DD)
    - Current Time: {{CURRENT_TIME}} (Format: HH:MM:SS)

    Rules:
    - Ignore greetings and unrelated conversation.
    - If multiple expenses are mentioned, return all as an array of JSON objects.
    - Amount must be numeric. Never invent values.
    - If uncertain about an amount, return null.
    - Category must come from the supplied category list.
    - Payment method must come from the supplied payment methods.
    - If no date is spoken, use Today's Date ({{CURRENT_DATE}}).
    - If no time is spoken, use Current Time ({{CURRENT_TIME}}).
    - Do not create duplicate transactions for repeated statements unless they clearly describe separate payments.
    - Add the primary item name as "description". Any extra context goes in "notes".
    - Return ONLY a JSON array of objects:

    [
    {
        "amount": 0,
        "date": "YYYY-MM-DD",
        "description": null,
        "category_id": 0,
        "user_id": 0,
        "time": "HH:MM:SS",
        "payment_method_id": null,
        "account_id": null,
        "notes": null
    }
    ]

    Available categories:
    {{CATEGORIES}}

    Payment methods:
    0: Cash
    1: Debit Card
    2: Bank Transfer
    3: USSD
    """

    current_date = datetime.now().strftime("%Y-%m-%d")
    current_time = datetime.now().strftime("%H:%M:%S")

    prompt = prompt_template.replace("{{CURRENT_DATE}}", current_date).replace(
        "{{CURRENT_TIME}}", current_time
    ).replace(
        "{{CATEGORIES}}",
        "\n".join(f"{category['id']}: {category['name']}" for category in categories),
    )

    try: 
        response = client.models.generate_content(
            model="gemini-3.1-flash-lite",
            contents = [uploaded, prompt],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema = list[ExpenseCreate]
            )  
        )

        
    
    except ClientError as e:
        logger.exception("Gemini API error")
        raise HTTPException(status_code=500, detail="Gemini API error: " + str(e))
    
    finally:
        try:
            client.files.delete(name=uploaded.name)
        except ClientError as e:
            logger.exception("Failed to delete uploaded file: " + str(e))

    return response.parsed
import json
import time
from dotenv import load_dotenv
from fastapi import logger, HTTPException
from google import genai
from google.genai import types
from google.genai.errors import ClientError
import os

from tenacity import retry, stop_after_attempt, wait_fixed

from schemas.expense import ExpenseCreate

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def extract_transaction(audio_path: str):
    timeout = 60  # seconds
    start = time.time()
    # perf_time = time.perf_counter()
    
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
            raise Exception("File processing failed")
                
        if time.time() - start > timeout:
            raise TimeoutError("File processing timed out")
        
        time.sleep(2)  # Wait for a second before checking again

    
    prompt = """
    You are an intelligent financial assistant.
    Your goal is to extract one or more expenses from spoken language.
    Rules:
    - Ignore greetings.
    - Ignore unrelated conversation.
    - If multiple expenses are mentioned, return all.
    - Amount must be numeric.
    - Never invent values.
    - If uncertain, return null.
    - Category must come from the supplied category list.
    - Payment method must come from the supplied payment methods.
    - Use today's date if no date is spoken.
    - Use the current time if no time is spoken.
    - Do not create duplicate transactions for repeated statements unless they clearly describe separate payments.
    - Add item only as description, any other details should be in notes.
    - Return ONLY JSON:

    {
        "amount": 0,
        "date": null,
        "description": null,
        "category_id": 0,
        "user_id": 0,
        "time": null,
        "payment_method_id": null,
        "account_id": null,
        "notes": null
    }

    Available categories:
    2: utilities
    3: housing
    4: food & groceries
    5: transportation
    6: health care & medical
    7: personal & family care
    8: entertainment & subscriptions
    9: financial obligations & savings
    10: miscellaneous

    Payment methods:
    1 Cash
    2 Debit Card
    3 Credit Card
    4 Bank Transfer
    5 Mobile Money

    Use current date and time for the "date" and "time" fields. If any field is not present in the audio, set it to null or 0 as appropriate.
    """

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

    # logger.info(
    # "Expense extraction took %.2f seconds",
    # time.perf_counter() - perf_time
    # )

    return response.parsed
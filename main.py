from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import PlainTextResponse
import os
from datetime import datetime
import json
from google import genai
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")

def get_gemini_client():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="GEMINI_API_KEY environment variable is not set."
        )
    return genai.Client(api_key=api_key)


@app.get("/", response_class=PlainTextResponse)
async def verify_webhook(
    request: Request,
):
    params = request.query_params

    mode = params.get("hub.mode")
    challenge = params.get("hub.challenge")
    token = params.get("hub.verify_token")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        print("WEBHOOK VERIFIED")
        return challenge

    raise HTTPException(status_code=403)


@app.post("/")
async def receive_webhook(request: Request):
    body = await request.json()

    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n\nWebhook received {timestamp}\n")
    print(json.dumps(body, indent=2))

    return {"status": "ok"}


@app.post("/chat-webhook")
async def chat_webhook(request: Request):
    body = await request.json()
    
    print("\n[Google Chat Webhook Event Received]")
    print(json.dumps(body, indent=2))
    
    # Check if the payload is in the Google Workspace Add-on format
    is_addon_format = "chat" in body and "commonEventObject" in body
    
    user_message_text = ""
    event_type = body.get("type")
    
    if is_addon_format:
        # Extract text from Workspace Add-on format
        message_payload = body.get("chat", {}).get("messagePayload", {})
        message = message_payload.get("message", {})
        user_message_text = message.get("text", "")
        
        # If text is empty, check fallback fields
        if not user_message_text:
            user_message_text = message.get("argumentText", "")
    else:
        # Standard Google Chat App format
        if event_type == "ADDED_TO_SPACE":
            return {
                "text": "Hello! I am a Gemini-powered Google Chat bot. Ask me anything!"
            }
        elif event_type == "MESSAGE":
            message = body.get("message", {})
            user_message_text = message.get("text", "")
            
    # Process with Gemini if we have a prompt
    if user_message_text:
        try:
            client = get_gemini_client()
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=user_message_text
            )
            response_text = response.text
        except Exception as e:
            print(f"Error calling Gemini API: {e}")
            response_text = f"Error processing request: {str(e)}"
    else:
        response_text = "I received an event but couldn't find a message to respond to."
        
    # Return response in the correct format matching the request
    if is_addon_format:
        return {
            "hostAppDataAction": {
                "chatDataAction": {
                    "createMessageAction": {
                        "message": {
                            "text": response_text
                        }
                    }
                }
            }
        }
    else:
        return {
            "text": response_text
        }

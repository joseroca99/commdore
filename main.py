from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import PlainTextResponse
import os
from datetime import datetime
import json

app = FastAPI()

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")

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
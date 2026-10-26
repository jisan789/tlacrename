import os
import sys
import time
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, status
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
import httpx
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.functions.account import UpdateProfileRequest

import config

client: TelegramClient | None = None
START_TIME = time.time()

async def background_pinger():
    """Background task to periodically ping /ping to prevent service sleep on Render."""
    await asyncio.sleep(5)
    port = os.getenv("PORT", "8000")
    interval = int(os.getenv("PING_INTERVAL", "600"))

    while True:
        base_url = os.getenv("PING_URL") or os.getenv("RENDER_EXTERNAL_URL")
        if base_url:
            target_url = base_url.rstrip("/") + "/ping" if not base_url.endswith("/ping") else base_url
        else:
            target_url = f"http://127.0.0.1:{port}/ping"

        try:
            async with httpx.AsyncClient(timeout=15.0) as http_client:
                res = await http_client.get(target_url)
                print(f"[Pinger] Pinged {target_url} -> Status {res.status_code}")
        except Exception as e:
            print(f"[Pinger] Ping to {target_url} failed: {e}")

        await asyncio.sleep(interval)

@asynccontextmanager
async def lifespan(app: FastAPI):
    global client
    print("Connecting to Telegram...")
    client = TelegramClient(StringSession(config.SESSION_STRING), config.API_ID, config.API_HASH)
    try:
        await client.connect()
        if await client.is_user_authorized():
            me = await client.get_me()
            print(f"Telegram connected as {me.first_name} {me.last_name or ''}".strip())
        else:
            print("Telegram client session is not authorized.")
    except Exception as e:
        print(f"Error connecting to Telegram: {e}", file=sys.stderr)

    pinger_task = asyncio.create_task(background_pinger())
    yield
    pinger_task.cancel()
    if client:
        try:
            await client.disconnect()
        except Exception:
            pass

DESCRIPTION = """
### Telegram Account Name API

This service connects directly to Telegram MTProto via a Telethon StringSession.
It allows you to:
- **View current account name** (`GET /name`)
- **Update account name** directly on Telegram (`POST /name`)
- **Ping / Keepalive** health checks to prevent cloud services (like Render) from sleeping (`GET /ping`)
"""

app = FastAPI(
    title="Telegram Account Name Service",
    description=DESCRIPTION,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Static files
static_dir = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir, exist_ok=True)

app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Models for Swagger /docs
class NameResponse(BaseModel):
    name: str = Field(..., description="Full display name (first + last)", example="Galif")
    first_name: str = Field(..., description="First name of the Telegram account", example="Galif")
    last_name: str = Field(..., description="Last name of the Telegram account", example="")

class NameUpdateRequest(BaseModel):
    name: str | None = Field(None, description="Full name string. Automatically split into first and last name if provided.", example="Alex Smith")
    first_name: str | None = Field(None, description="Explicit first name", example="Alex")
    last_name: str | None = Field(None, description="Explicit last name", example="Smith")

class UpdateSuccessResponse(BaseModel):
    success: bool = Field(True, example=True)
    message: str = Field("Account name updated successfully", example="Account name updated successfully")
    name: str = Field(..., example="Alex Smith")
    first_name: str = Field(..., example="Alex")
    last_name: str = Field(..., example="Smith")

class PingResponse(BaseModel):
    status: str = Field("pong", example="pong")
    message: str = Field("Service is alive", example="Service is alive")
    uptime_seconds: int = Field(..., example=120)
    timestamp: float = Field(..., example=1793019242.22)


@app.api_route("/", methods=["GET", "HEAD"], include_in_schema=False)
async def root():
    """Serves the minimal Web UI displaying account name."""
    return FileResponse(os.path.join(static_dir, "index.html"))

@app.get("/ping", response_model=PingResponse, tags=["Health & Keepalive"], summary="Ping Keepalive & Health Check")
@app.head("/ping", include_in_schema=False)
async def ping():
    """
    Returns server status, uptime, and timestamp.
    Used by internal background pinger and external uptime monitors to keep Render alive.
    """
    uptime_seconds = int(time.time() - START_TIME)
    return {
        "status": "pong",
        "message": "Service is alive",
        "uptime_seconds": uptime_seconds,
        "timestamp": time.time()
    }

@app.get(
    "/name",
    response_model=NameResponse,
    tags=["Telegram Account"],
    summary="Get Telegram Account Name"
)
async def get_name():
    """
    Retrieves the current first and last name of the logged-in Telegram account.
    """
    global client
    if not client or not client.is_connected():
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Telegram client not connected")

    try:
        me = await client.get_me()
        full_name = f"{me.first_name or ''} {me.last_name or ''}".strip()
        return {
            "name": full_name,
            "first_name": me.first_name or "",
            "last_name": me.last_name or ""
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@app.post(
    "/name",
    response_model=UpdateSuccessResponse,
    tags=["Telegram Account"],
    summary="Update Telegram Account Name"
)
async def update_name(req: NameUpdateRequest):
    """
    Updates the Telegram account's name via MTProto `UpdateProfileRequest`.
    
    You can provide:
    - `name`: Full name string (e.g. `"John Doe"`), OR
    - `first_name` and `last_name` separately.
    """
    global client
    if not client or not client.is_connected():
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Telegram client not connected")

    first_name = req.first_name
    last_name = req.last_name

    if req.name is not None:
        trimmed = req.name.strip()
        if not trimmed:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Account name cannot be empty")
        parts = trimmed.split(" ", 1)
        first_name = parts[0]
        last_name = parts[1] if len(parts) > 1 else ""

    if not first_name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="First name cannot be empty")

    try:
        updated_user = await client(UpdateProfileRequest(
            first_name=first_name,
            last_name=last_name or ""
        ))
        full_name = f"{updated_user.first_name or ''} {updated_user.last_name or ''}".strip()
        return {
            "success": True,
            "message": "Account name updated successfully",
            "name": full_name,
            "first_name": updated_user.first_name or "",
            "last_name": updated_user.last_name or ""
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to update Telegram name: {str(e)}")

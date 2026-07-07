import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel

from app.config import settings
from app.services.tts_service import tts_service

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger(__name__)


class TTSRequest(BaseModel):
    text: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting %s", settings.app_name)
    await asyncio.to_thread(tts_service.initialize)
    logger.info("TTS service ready")
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/ready")
def ready() -> dict:
    return {"ready": tts_service.ready}


@app.post("/tts/am")
async def tts_am(payload: TTSRequest) -> Response:
    if not tts_service.ready:
        raise HTTPException(status_code=503, detail="TTS model is not ready")
    try:
        wav_bytes = await asyncio.to_thread(tts_service.generate, payload.text)
    except Exception as exc:
        logger.exception("TTS failed")
        raise HTTPException(status_code=500, detail="TTS processing failed") from exc
    if not wav_bytes:
        raise HTTPException(status_code=400, detail="Input produced no audio")
    return Response(content=wav_bytes, media_type="audio/wav")

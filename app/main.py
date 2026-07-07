import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel

from app.config import settings
from app.services import registry  # noqa: F401 — triggers __init__ registration
from app.services import registry as svc_registry

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
    languages = svc_registry.all_languages()
    for lang in languages:
        service = svc_registry.get(lang)
        logger.info("Initializing TTS service for language: %s", lang)
        await asyncio.to_thread(service.initialize)
        logger.info("TTS service ready for language: %s", lang)
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/ready")
def ready() -> dict:
    return {lang: svc_registry.get(lang).ready for lang in svc_registry.all_languages()}


@app.post("/tts/{lang}")
async def tts(lang: str, payload: TTSRequest) -> Response:
    try:
        service = svc_registry.get(lang)
    except KeyError as kerr:
        raise HTTPException(
            status_code=404,
            detail=f"No TTS service for language: '{lang}'. "
            f"Available: {svc_registry.all_languages()}",
        ) from kerr

    if not service.ready:
        raise HTTPException(
            status_code=503, detail=f"TTS service for '{lang}' is not ready"
        )

    try:
        wav_bytes = await asyncio.to_thread(service.generate, payload.text)
    except Exception as exc:
        logger.exception("TTS failed for language: %s", lang)
        raise HTTPException(status_code=500, detail="TTS processing failed") from exc

    if not wav_bytes:
        raise HTTPException(status_code=400, detail="Input produced no audio")

    return Response(content=wav_bytes, media_type="audio/wav")

from __future__ import annotations

import io
import logging
import re
from pathlib import Path

import soundfile as sf
import torch
from omnivoice import OmniVoice, OmniVoiceGenerationConfig
from pydub import AudioSegment

from app.config import settings
from app.services.base import BaseTTSService
from app.utils.audio import export_wav, trim_leading_trailing_silence

logger = logging.getLogger(__name__)


class AmharicTTSService(BaseTTSService):
    def __init__(self) -> None:
        self.model: OmniVoice | None = None
        self.voice_clone_prompt = None
        self.ready = False

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def initialize(self) -> None:
        logger.info("Loading Amharic TTS: %s", settings.amharic_tts_model)

        device = self._torch_device()
        self.model = OmniVoice.from_pretrained(
            settings.amharic_tts_model,
            device_map="auto" if device == "cuda" else "cpu",
            dtype=torch.float16 if device == "cuda" else torch.float32,
            attn_implementation="eager",
        )

        ref_wav = Path(settings.amharic_voice_reference_path)
        ref_txt = Path(settings.amharic_voice_reference_text_path)

        if not ref_wav.exists():
            raise RuntimeError(f"Reference voice WAV not found: {ref_wav}")
        if not ref_txt.exists():
            raise RuntimeError(f"Reference voice transcript not found: {ref_txt}")

        ref_text = ref_txt.read_text(encoding="utf-8").strip()
        if not ref_text:
            raise RuntimeError(f"Reference voice transcript is empty: {ref_txt}")

        logger.info("Creating voice clone prompt from %s", ref_wav.name)
        self.voice_clone_prompt = self.model.create_voice_clone_prompt(
            ref_audio=str(ref_wav),
            ref_text=ref_text,
        )

        self.ready = True
        logger.info("Amharic TTS ready")

    # ------------------------------------------------------------------
    # Public API (satisfies BaseTTSService)
    # ------------------------------------------------------------------

    def generate(self, text: str) -> bytes:
        if not self.ready:
            raise RuntimeError("TTS model is not loaded")

        from app.utils.text_normalizer import normalize_text_for_tts

        safe_text = normalize_text_for_tts(text, "am")
        if not safe_text:
            return b""

        chunks = self._split_chunks(safe_text)
        if not chunks:
            return b""

        if len(chunks) == 1:
            return self._generate_chunk(chunks[0])

        return self._stitch_chunks(chunks)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _torch_device(self) -> str:
        if settings.tts_device == "auto":
            return "cuda" if torch.cuda.is_available() else "cpu"
        return settings.tts_device

    def _split_chunks(self, text: str) -> list[str]:
        max_chars = max(40, settings.amharic_tts_chunk_chars)
        normalized = re.sub(r"\s+", " ", text).strip()
        if not normalized:
            return []

        sentence_parts = re.split(r"(?<=[።፧!?])\s+|\n+", normalized)
        chunks: list[str] = []
        current = ""
        for part in [p.strip() for p in sentence_parts if p.strip()]:
            candidate = f"{current} {part}".strip() if current else part
            if len(candidate) <= max_chars:
                current = candidate
                continue
            if current:
                chunks.append(current)
            current = ""
            if len(part) <= max_chars:
                current = part
                continue
            for idx in range(0, len(part), max_chars):
                subchunk = part[idx : idx + max_chars].strip()
                if subchunk:
                    chunks.append(subchunk)
        if current:
            chunks.append(current)
        return chunks

    def _generate_chunk(self, text: str) -> bytes:
        config = OmniVoiceGenerationConfig(
            num_step=32,
            guidance_scale=2.0,
            postprocess_output=True,
        )
        with torch.inference_mode():
            audio = self.model.generate(
                text=text,
                language="Amharic",
                voice_clone_prompt=self.voice_clone_prompt,
                generation_config=config,
            )
        buffer = io.BytesIO()
        sf.write(buffer, audio[0], 24000, format="WAV")
        return buffer.getvalue()

    def _stitch_chunks(self, chunks: list[str]) -> bytes:
        pause = AudioSegment.silent(
            duration=max(0, settings.amharic_tts_chunk_pause_ms)
        )
        stitched = AudioSegment.empty()

        for i, chunk in enumerate(chunks):
            logger.info("TTS chunk %d/%d: %s", i + 1, len(chunks), chunk[:40])
            chunk_bytes = self._generate_chunk(chunk)
            audio = AudioSegment.from_file(io.BytesIO(chunk_bytes), format="wav")
            audio = trim_leading_trailing_silence(audio)
            if i > 0 and len(pause) > 0:
                stitched += pause
            stitched += audio

        return export_wav(trim_leading_trailing_silence(stitched))

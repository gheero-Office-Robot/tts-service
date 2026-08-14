import os
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "BOA TTS Service"

    hf_home: str = "/models/hf_cache"
    model_cache_dir: str = "/models/cache"

    tts_cuda_device: int = 0
    tts_warmup_text: str = (
        "ሰላም፣ ይህ የድምፅ ማሞቂያ ሙከራ ነው።"
    )

    amharic_tts_model: str = "african-low-resource/omnivoice-amharic"
    amharic_voice_reference_path: str = str(
        Path(__file__).resolve().parents[1]
        / "assets/voices/amharic_reference_voice.wav"
    )
    amharic_voice_reference_text_path: str = str(
        Path(__file__).resolve().parents[1]
        / "assets/voices/amharic_reference_voice.txt"
    )
    amharic_tts_chunk_chars: int = 140
    amharic_tts_chunk_pause_ms: int = 120

    request_timeout_seconds: int = 300

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"


settings = Settings()
os.environ.setdefault("HF_HOME", settings.hf_home)

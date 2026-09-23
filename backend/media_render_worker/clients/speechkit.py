"""Синтез речи через Yandex SpeechKit (те же модели голоса, что у Алисы).

API v1 отдаёт LPCM без WAV-заголовка на format=lpcm (16 бит, little-endian,
моно) — заголовок дописываем сами модулем wave, чтобы Replicate получил файл,
который однозначно опознаётся как аудио."""

import io
import wave

import httpx

from core.config import settings

_ENDPOINT = "https://tts.api.cloud.yandex.net/speech/v1/tts:synthesize"
_SAMPLE_RATE = 48000

# code в VoiceStyle (media_service) -> голос SpeechKit.
VOICE_BY_STYLE = {
    "era_male": "ermil",
    "era_female": "jane",
    "neutral": "filipp",
}


def synthesize(text: str, voice_style: str) -> bytes:
    """Текст -> WAV-байты (моно, 16 бит, 48 кГц)."""
    voice = VOICE_BY_STYLE.get(voice_style, "filipp")
    response = httpx.post(
        _ENDPOINT,
        headers={"Authorization": f"Api-Key {settings.yandex_api_key}"},
        data={
            "text": text,
            "lang": "ru-RU",
            "voice": voice,
            "format": "lpcm",
            "sampleRateHertz": str(_SAMPLE_RATE),
            "folderId": settings.yandex_folder_id,
        },
        timeout=settings.upstream_timeout_seconds,
    )
    response.raise_for_status()
    return _wrap_wav(response.content)


def _wrap_wav(pcm: bytes) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(_SAMPLE_RATE)
        wav_file.writeframes(pcm)
    return buf.getvalue()

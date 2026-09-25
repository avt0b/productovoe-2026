import wave
from io import BytesIO

import httpx
import pytest

from clients import speechkit
from clients.speechkit import _wrap_wav
from core.errors import RenderFailed


def test_wrap_wav_produces_valid_wav_header():
    pcm = (b"\x00\x01" * 100) * 2  # 16-бит семплы, произвольные данные
    wav_bytes = _wrap_wav(pcm)

    with wave.open(BytesIO(wav_bytes), "rb") as wav_file:
        assert wav_file.getnchannels() == 1
        assert wav_file.getsampwidth() == 2
        assert wav_file.getframerate() == 48000
        assert wav_file.readframes(wav_file.getnframes()) == pcm


def test_rejected_key_is_explained(monkeypatch):
    def post(url, **kwargs):
        return httpx.Response(
            401,
            json={"error_code": "UNAUTHORIZED", "error_message": "Unknown api key"},
            request=httpx.Request("POST", url),
        )

    monkeypatch.setattr(speechkit.httpx, "post", post)
    with pytest.raises(RenderFailed, match="SpeechKit: ключ не принят"):
        speechkit.synthesize("Помни меня.", "era_male")

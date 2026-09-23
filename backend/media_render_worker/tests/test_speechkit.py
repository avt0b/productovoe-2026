import wave
from io import BytesIO

from clients.speechkit import _wrap_wav


def test_wrap_wav_produces_valid_wav_header():
    pcm = (b"\x00\x01" * 100) * 2  # 16-бит семплы, произвольные данные
    wav_bytes = _wrap_wav(pcm)

    with wave.open(BytesIO(wav_bytes), "rb") as wav_file:
        assert wav_file.getnchannels() == 1
        assert wav_file.getsampwidth() == 2
        assert wav_file.getframerate() == 48000
        assert wav_file.readframes(wav_file.getnframes()) == pcm

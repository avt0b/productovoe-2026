from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from core.models import ClipStatus, VoiceStyle


class ClipCreate(BaseModel):
    soldier_name: str = Field(default="", max_length=255)
    source_photo_url: str = Field(min_length=1, max_length=500)
    narration_text: str = Field(
        default="Я сделал это, чтобы ты жил и видел голубое небо. Помни меня.",
        max_length=2000,
    )
    voice_style: VoiceStyle = VoiceStyle.era_male
    is_public: bool = False
    archive_entry_id: str | None = Field(default=None, max_length=36)
    # Этическая оговорка ТЗ — обязательное согласие.
    consent_memorial_use: bool


class ClipUpdate(BaseModel):
    soldier_name: str | None = Field(default=None, max_length=255)
    narration_text: str | None = Field(default=None, max_length=2000)
    voice_style: VoiceStyle | None = None
    is_public: bool | None = None

    def to_update_dict(self) -> dict:
        return self.model_dump(exclude_unset=True)


class ClipOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    soldier_name: str
    source_photo_url: str
    narration_text: str
    voice_style: VoiceStyle
    submitted_by: str
    consent_memorial_use: bool
    is_public: bool
    status: ClipStatus
    video_url: str | None
    error: str
    rendered_at: datetime | None
    archive_entry_id: str | None
    created_at: datetime


class MarkReadyRequest(BaseModel):
    video_url: str = Field(min_length=1, max_length=500)


class MarkFailedRequest(BaseModel):
    error: str = Field(min_length=1, max_length=1000)


class ShareCreate(BaseModel):
    recipient: str = Field(min_length=1, max_length=300)
    note: str = Field(default="", max_length=1000)


class ShareOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    clip_id: str
    shared_by: str
    recipient: str
    note: str
    created_at: datetime

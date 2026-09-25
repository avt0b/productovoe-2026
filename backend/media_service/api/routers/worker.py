from fastapi import APIRouter, Depends, Response, status

from api.deps import ClipServiceDep, require_render_worker
from api.schemas.clip import ClipOut, MarkFailedRequest, MarkReadyRequest

router = APIRouter(
    prefix="/render",
    tags=["render worker (переходы состояний)"],
    dependencies=[Depends(require_render_worker)],
)


@router.post("/claim", response_model=ClipOut | None)
def claim_next(service: ClipServiceDep, response: Response) -> ClipOut | None:
    """Забрать самый старый клип из очереди: queued -> processing."""
    clip = service.claim_next()
    if clip is None:
        response.status_code = status.HTTP_204_NO_CONTENT
        return None
    return ClipOut.model_validate(clip)


@router.post("/{clip_id}/ready", response_model=ClipOut)
def mark_ready(clip_id: str, payload: MarkReadyRequest, service: ClipServiceDep) -> ClipOut:
    return ClipOut.model_validate(service.mark_ready(clip_id, video_url=payload.video_url))


@router.post("/{clip_id}/failed", response_model=ClipOut)
def mark_failed(clip_id: str, payload: MarkFailedRequest, service: ClipServiceDep) -> ClipOut:
    return ClipOut.model_validate(service.mark_failed(clip_id, error=payload.error))

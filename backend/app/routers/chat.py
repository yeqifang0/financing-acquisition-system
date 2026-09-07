"""Chat 路由：SSE 流式对话流水线。"""
import json
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from ..schemas import ChatRequest
from ..services import run_pipeline

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/stream")
def chat_stream(req: ChatRequest):
    """SSE 流式响应：text/params/steps/step/log/card/done/error 事件。"""
    def gen():
        for chunk in run_pipeline(req.message):
            yield chunk
    return StreamingResponse(
        gen(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )

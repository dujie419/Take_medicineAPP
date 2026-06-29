import base64
import json
import time
from io import BytesIO
from pathlib import Path
from uuid import uuid4

import httpx
from fastapi import HTTPException, UploadFile, status
from PIL import Image, UnidentifiedImageError
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.config import PROJECT_ROOT, get_settings
from app.models.ai_recognition_record import AiRecognitionRecord
from app.schemas.medicine import MedicineRecognitionResult


ALLOWED_IMAGE_FORMATS = {
    "JPEG": ("image/jpeg", ".jpg"),
    "PNG": ("image/png", ".png"),
    "WEBP": ("image/webp", ".webp"),
}


class AiRecognitionService:
    def __init__(self, db: Session):
        self.db = db
        self.settings = get_settings()

    async def recognize(self, user_id: int, upload: UploadFile) -> tuple[AiRecognitionRecord, MedicineRecognitionResult]:
        image_bytes = await self._read_and_validate_upload(upload)
        image_path = self._save_image(user_id, image_bytes)
        record = AiRecognitionRecord(
            user_id=user_id,
            image_path=image_path,
            recognition_mode=self.settings.ai_recognition_mode,
            status="pending",
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)

        started_at = time.perf_counter()
        raw_response = None
        try:
            raw_response = await self._call_ai(image_bytes)
            result = self._parse_result(raw_response)
        except Exception as exc:
            record.status = "failed"
            record.raw_response = raw_response
            record.error_message = self._friendly_error(exc)
            record.duration_ms = self._elapsed_ms(started_at)
            self.db.commit()
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=record.error_message) from exc

        record.status = "success"
        record.raw_response = raw_response
        record.structured_result = result.model_dump()
        record.duration_ms = self._elapsed_ms(started_at)
        self.db.commit()
        self.db.refresh(record)
        return record, result

    async def _read_and_validate_upload(self, upload: UploadFile) -> bytes:
        max_size = self.settings.max_upload_size_mb * 1024 * 1024
        image_bytes = await upload.read()
        if not image_bytes:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="请上传图片文件")
        if len(image_bytes) > max_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"图片不能超过 {self.settings.max_upload_size_mb}MB",
            )

        try:
            with Image.open(BytesIO(image_bytes)) as image:
                image.verify()
                if image.format not in ALLOWED_IMAGE_FORMATS:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="仅支持 JPEG、PNG、WebP 图片")
        except UnidentifiedImageError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="无法识别图片格式") from exc

        return image_bytes

    def _save_image(self, user_id: int, image_bytes: bytes) -> str:
        with Image.open(BytesIO(image_bytes)) as image:
            _, extension = ALLOWED_IMAGE_FORMATS[image.format]

        relative_dir = Path(self.settings.upload_dir) / f"user_{user_id}" / "recognition"
        absolute_dir = PROJECT_ROOT / relative_dir
        absolute_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{uuid4().hex}{extension}"
        absolute_path = absolute_dir / filename
        absolute_path.write_bytes(image_bytes)
        return (relative_dir / filename).as_posix()

    async def _call_ai(self, image_bytes: bytes) -> dict:
        mode = self.settings.ai_recognition_mode.lower()
        if mode == "mock":
            return self._mock_response()
        if mode == "bailian":
            return await self._call_bailian(image_bytes)
        raise ValueError("AI_RECOGNITION_MODE 仅支持 mock 或 bailian")

    def _mock_response(self) -> dict:
        return {
            "document_type": "药盒",
            "medicines": [
                {
                    "name": "阿司匹林肠溶片",
                    "specification": "100mg * 30片",
                    "dosage": "每次 1 片",
                    "daily_times": 1,
                    "suggested_times": ["08:00"],
                    "usage_note": "饭后服用，请按医生或药师指导确认",
                    "confidence": 0.86,
                    "risk_notice": "请核对药盒、说明书或医生处方",
                    "need_confirm": True,
                }
            ],
            "overall_risk_notice": "AI识别结果仅供参考，请人工确认",
        }

    async def _call_bailian(self, image_bytes: bytes) -> dict:
        if not self.settings.bailian_api_key:
            raise ValueError("未配置 BAILIAN_API_KEY")

        return await self._call_bailian_model(image_bytes)

    async def _call_bailian_model(self, image_bytes: bytes) -> dict:
        image_data = base64.b64encode(image_bytes).decode("ascii")
        payload = {
            "model": self.settings.bailian_model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": self._recognition_prompt()},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}},
                    ],
                }
            ],
            "temperature": 0.1,
        }
        headers = {
            "Authorization": f"Bearer {self.settings.bailian_api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        content = data["choices"][0]["message"]["content"]
        return self._extract_json(content)

    def _recognition_prompt(self) -> str:
        return (
            "请识别图片中的药盒、药瓶、处方或用药清单，只返回 JSON，不要输出 Markdown。"
            "JSON 字段必须包含 document_type、medicines、overall_risk_notice；"
            "medicines 每项必须包含 name、specification、dosage、daily_times、suggested_times、"
            "usage_note、confidence、risk_notice、need_confirm。"
            "如果无法确认药品名称，medicines 返回空数组。"
            "不要输出诊断、停药、换药、剂量调整或处方调整建议。"
        )

    def _extract_json(self, content: str | dict) -> dict:
        if isinstance(content, dict):
            return content
        text = content.strip()
        if text.startswith("```"):
            text = text.strip("`").removeprefix("json").strip()
        return json.loads(text)

    def _parse_result(self, raw_response: dict) -> MedicineRecognitionResult:
        try:
            return MedicineRecognitionResult.model_validate(raw_response)
        except ValidationError as exc:
            raise ValueError("AI 返回结构不符合要求") from exc

    def _friendly_error(self, exc: Exception) -> str:
        if isinstance(exc, httpx.TimeoutException):
            return "AI 识别超时，请稍后重试"
        if isinstance(exc, httpx.HTTPStatusError):
            return "AI 服务返回异常，请稍后重试"
        if isinstance(exc, (json.JSONDecodeError, KeyError, IndexError, ValidationError)):
            return "AI 返回格式异常，请人工添加药品"
        return str(exc) or "AI 识别失败，请稍后重试"

    def _elapsed_ms(self, started_at: float) -> int:
        return int((time.perf_counter() - started_at) * 1000)

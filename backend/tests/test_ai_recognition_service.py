from io import BytesIO

import pytest
from fastapi import HTTPException, UploadFile
from PIL import Image

from app.schemas.medicine import MedicineRecognitionResult
from app.services.ai_recognition_service import AiRecognitionService


def make_upload(filename: str, content: bytes, content_type: str) -> UploadFile:
    return UploadFile(filename=filename, file=BytesIO(content), headers={"content-type": content_type})


def make_png_bytes() -> bytes:
    output = BytesIO()
    Image.new("RGB", (8, 8), color="white").save(output, format="PNG")
    return output.getvalue()


def test_mock_response_matches_recognition_schema() -> None:
    service = AiRecognitionService.__new__(AiRecognitionService)
    result = MedicineRecognitionResult.model_validate(service._mock_response())

    assert result.document_type == "药盒"
    assert result.medicines[0].name == "阿司匹林肠溶片"
    assert result.medicines[0].need_confirm is True


@pytest.mark.asyncio
async def test_upload_validation_accepts_png_image() -> None:
    service = AiRecognitionService(db=None)
    upload = make_upload("medicine.png", make_png_bytes(), "image/png")

    image_bytes = await service._read_and_validate_upload(upload)

    assert image_bytes


@pytest.mark.asyncio
async def test_upload_validation_rejects_non_image_file() -> None:
    service = AiRecognitionService(db=None)
    upload = make_upload("medicine.txt", b"not an image", "text/plain")

    with pytest.raises(HTTPException) as exc_info:
        await service._read_and_validate_upload(upload)

    assert exc_info.value.status_code == 400

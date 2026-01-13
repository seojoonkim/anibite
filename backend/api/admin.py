"""
Admin API Router
관리자 기능 (이미지 업로드 등)
"""
from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import boto3
import os
from typing import List

router = APIRouter()

# R2 Configuration from environment
R2_ENDPOINT = os.getenv('R2_ENDPOINT', 'https://4c992c8bb965837b720321f2230b4952.r2.cloudflarestorage.com')
R2_ACCESS_KEY = os.getenv('R2_ACCESS_KEY', 'e4e50bad9af8e8f39a32cc9d8dd2bdc3')
R2_SECRET_KEY = os.getenv('R2_SECRET_KEY', 'e046d9a6c9aa0c18c69f0c756b1fd2cd3bcf5a08c9ac98c56937dec66d40bf5a')
R2_BUCKET = os.getenv('R2_BUCKET', 'anipass')

# Initialize S3 client for R2
s3_client = boto3.client(
    's3',
    endpoint_url=R2_ENDPOINT,
    aws_access_key_id=R2_ACCESS_KEY,
    aws_secret_access_key=R2_SECRET_KEY,
    region_name='auto'
)


@router.post("/upload-to-r2")
async def upload_to_r2(
    file: UploadFile = File(...),
    path: str = None
):
    """
    Upload file to R2

    - **file**: File to upload
    - **path**: R2 path (e.g., "characters/198.jpg")
    """
    try:
        if not path:
            raise HTTPException(status_code=400, detail="Path parameter is required")

        # Read file content
        content = await file.read()

        # Upload to R2
        s3_client.put_object(
            Bucket=R2_BUCKET,
            Key=path,
            Body=content,
            ContentType=file.content_type or 'application/octet-stream'
        )

        return JSONResponse(
            status_code=200,
            content={
                "message": "File uploaded successfully",
                "path": f"/{path}",
                "size": len(content)
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

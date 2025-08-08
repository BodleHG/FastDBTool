from pydantic import BaseModel
from typing import Optional
from abc import ABC, abstractmethod
import asyncio
import queue

class DBSelect(BaseModel):
    """DB Query Model : For Post

    Required Value: 
        table: str
        columns: list
        filters: dict
    """
    
    table: str
    columns: Optional[list] = None
    filters: Optional[dict] = None

class DBInsert(BaseModel):
    """DB Insert Model : For Post

    Required Value: 
        table: str
        data: dict
    """
    
    table: str
    data: dict

class DBDelete(BaseModel):
    """DB Delete Model : For Post

    Required Value: 
        table: str
        filters: dict
    """
    
    table: str
    filters: dict
    
# Unity C#에서 전송받는 GLB 파일 데이터 모델
class GLBUploadRequest(BaseModel):
    name: str
    description: Optional[str] = ""
    data: str  # Base64 인코딩된 GLB 데이터

class GLBDownloadResponse(BaseModel):
    name: str
    description: str
    data: str  # Base64 인코딩된 GLB 데이터
    file_size: int
    success: bool = True
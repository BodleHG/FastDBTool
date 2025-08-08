from fastapi import APIRouter, Depends, Request, responses, status, Response, Body, FastAPI, File, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from typing import Dict, Any, Optional
from ..models.base_model import DBInsert, DBSelect, GLBUploadRequest, GLBDownloadResponse
from ..models.database import DBManager
import json
from .response_format import ResponseFormat
import queue
import io
import base64
import os
from pydantic import BaseModel

router = APIRouter()
db_manager = DBManager()


# GLB 파일 바이너리 업로드 (바이너리 형태로 직접 받기)
@router.post("/upload-glb/", response_model=Dict[str, Any])
async def upload_glb_binary(
    file: UploadFile = File(...),
    name: Optional[str] = None,
    description: Optional[str] = ""
):
    table = "GLB"
    try:
        # 파일명 설정
        if not name:
            name = file.filename
        
        # 파일 확장자 검증
        if not file.filename.lower().endswith('.glb'):
            return JSONResponse(
                status_code=400,
                content={"error": "파일명은 .glb 확장자여야 합니다."}
            )
        
        # 파일 데이터 읽기
        file_data = await file.read()
        
        # GLB 파일 헤더 검증 (GLB 파일은 "glTF"로 시작)
        if len(file_data) < 4 or file_data[:4] != b'glTF':
            return JSONResponse(
                status_code=400,
                content={"error": "유효하지 않은 GLB 파일입니다."}
            )
        
        # 바이너리 데이터를 Base64로 인코딩하여 저장
        file_data_base64 = base64.b64encode(file_data).decode('utf-8')
        
        # 기존 테이블 구조에 맞춰 저장 (id, data, name, description)
        insert_data = {
            "data": file_data_base64,
            "name": name,
            "description": description
        }
        
        # 파라미터화된 쿼리를 사용하여 안전하게 데이터 삽입
        result = db_manager.insert_data(db_manager.json_to_sql_insert(table, insert_data))
        
        if result == "success":
            return {
                "success": True,
                "name": name,
                "description": description,
                "file_size": len(file_data),
                "message": "GLB 파일이 성공적으로 업로드되었습니다."
            }
        else:
            return JSONResponse(
                status_code=500,
                content={"error": f"데이터베이스 저장 실패: {result}"}
            )
            
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"파일 업로드 중 오류가 발생했습니다: {str(e)}"}
        )

# GLB 파일 다운로드 (Unity C# 호환)
@router.get("/download-glb/{file_id}", response_model=GLBDownloadResponse)
async def download_glb(file_id: int):
    try:
        db_manager = DBManager()
        
        # 파일 정보 조회
        select_sql = f"""
        SELECT id, name, data, description
        FROM glb_files 
        WHERE id = {file_id}
        """
        
        files = db_manager.get_data(select_sql)
        
        if not files:
            return JSONResponse(
                status_code=404,
                content={"error": "파일을 찾을 수 없습니다."}
            )
        
        file_info = files[0]
        
        # Base64 인코딩 (Unity C#에서 사용할 수 있도록)
        data_base64 = base64.b64encode(file_info['data']).decode('utf-8')
        
        # Unity C#에서 사용하기 적합한 응답 형태
        return GLBDownloadResponse(
            name=file_info['name'],
            description=file_info['description'],
            data=data_base64,
            file_size=len(file_info['data']),
            success=True
        )
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"파일 다운로드 중 오류가 발생했습니다: {str(e)}"}
        )

# GLB 파일 다운로드 (파일명 기반, Unity C# 호환)
@router.get("/download-glb-by-name/{filename}", response_model=GLBDownloadResponse)
async def download_glb_by_filename(filename: str):
    try:
        db_manager = DBManager()
        
        # 파일 정보 조회
        select_sql = f"""
        SELECT id, name, data, descriptio
        FROM glb_files 
        WHERE name = '{filename}'
        """
        
        files = db_manager.get_data(select_sql)
        
        if not files:
            return JSONResponse(
                status_code=404,
                content={"error": "파일을 찾을 수 없습니다."}
            )
        
        file_info = files[0]
        
        # Base64 인코딩 (Unity C#에서 사용할 수 있도록)
        data_base64 = base64.b64encode(file_info['data']).decode('utf-8')
        
        # Unity C#에서 사용하기 적합한 응답 형태
        return GLBDownloadResponse(
            name=file_info['name'],
            description=file_info['descriptio'],
            data=data_base64,
            file_size=len(file_info['data']),
            success=True
        )
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"파일 다운로드 중 오류가 발생했습니다: {str(e)}"}
        )

# GLB 파일 삭제
@router.delete("/delete-glb/{file_id}")
async def delete_glb_file(file_id: int):
    try:
        db_manager = DBManager()
        
        # 파일 존재 여부 확인
        check_sql = f"SELECT name FROM glb_files WHERE id = {file_id}"
        files = db_manager.get_data(check_sql)
        
        if not files:
            return JSONResponse(
                status_code=404,
                content={"error": "파일을 찾을 수 없습니다."}
            )
        
        # 파일 삭제
        delete_sql = f"DELETE FROM glb_files WHERE id = {file_id}"
        result = db_manager.insert_data(delete_sql)
        
        if result == "success":
            return {"success": True, "message": "파일이 성공적으로 삭제되었습니다."}
        else:
            return JSONResponse(
                status_code=500,
                content={"error": f"파일 삭제 실패: {result}"}
            )
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"파일 삭제 중 오류가 발생했습니다: {str(e)}"}
        )

# GLB 파일 정보 조회
@router.get("/glb-info/{file_id}")
async def get_glb_info(file_id: int):
    try:
        db_manager = DBManager()
        
        select_sql = f"""
        SELECT id, name, descriptio, LENGTH(data) as file_size
        FROM glb_files 
        WHERE id = {file_id}
        """
        
        files = db_manager.get_data(select_sql)
        
        if not files:
            return JSONResponse(
                status_code=404,
                content={"error": "파일을 찾을 수 없습니다."}
            )
        
        return {"success": True, "file_info": files[0]}
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"파일 정보 조회 중 오류가 발생했습니다: {str(e)}"}
        )

# Unity C#에서 사용할 수 있는 간단한 상태 확인 엔드포인트
@router.get("/health")
async def health_check():
    return {"status": "healthy", "message": "GLB 파일 서버가 정상적으로 작동 중입니다."}
#!/usr/bin/env python3
"""
GLB 파일을 MySQL에 저장하고 관리하는 사용 예시
"""

import asyncio
import aiofiles
import requests
from app.core.models.glb_database import GLBDatabaseManager

def test_glb_database_operations():
    """GLB 데이터베이스 작업 테스트"""
    
    # 데이터베이스 매니저 초기화
    db_manager = GLBDatabaseManager(
        host='localhost',
        port=3306,
        user='root',
        password='your_password',
        database='db_manager'
    )
    
    # 데이터베이스 연결
    if not db_manager.connect():
        print("데이터베이스 연결 실패")
        return
    
    try:
        # 1. GLB 파일 저장 테스트
        print("=== GLB 파일 저장 테스트 ===")
        
        # 테스트용 GLB 파일 데이터 (실제로는 파일에서 읽어옴)
        test_file_data = b"glTF\x02\x00\x00\x00..."  # 실제 GLB 파일 데이터
        
        file_id = db_manager.save_glb_file(
            filename="test_model.glb",
            file_data=test_file_data,
            description="테스트용 3D 모델",
            tags=["test", "model", "3d"],
            created_by="admin"
        )
        
        if file_id:
            print(f"파일 저장 성공: ID {file_id}")
        else:
            print("파일 저장 실패")
            return
        
        # 2. 파일 목록 조회 테스트
        print("\n=== 파일 목록 조회 테스트 ===")
        files = db_manager.list_glb_files(limit=10, offset=0)
        print(f"총 {len(files)}개 파일 발견:")
        for file in files:
            print(f"  - ID: {file['id']}, 파일명: {file['filename']}, 크기: {file['file_size']} bytes")
        
        # 3. 파일 메타데이터 조회 테스트
        print("\n=== 파일 메타데이터 조회 테스트 ===")
        file_info = db_manager.get_glb_file(file_id=file_id)
        if file_info:
            print(f"파일 정보: {file_info}")
        else:
            print("파일 정보 조회 실패")
        
        # 4. 파일 데이터 조회 테스트
        print("\n=== 파일 데이터 조회 테스트 ===")
        file_data = db_manager.get_glb_file_data(file_id=file_id)
        if file_data:
            print(f"파일 데이터 조회 성공: {len(file_data)} bytes")
        else:
            print("파일 데이터 조회 실패")
        
        # 5. 파일 정보 업데이트 테스트
        print("\n=== 파일 정보 업데이트 테스트 ===")
        success = db_manager.update_glb_file(
            file_id=file_id,
            description="업데이트된 테스트 모델",
            tags=["updated", "test", "model"],
            updated_by="admin"
        )
        if success:
            print("파일 정보 업데이트 성공")
        else:
            print("파일 정보 업데이트 실패")
        
        # 6. 파일 통계 조회 테스트
        print("\n=== 파일 통계 조회 테스트 ===")
        stats = db_manager.get_file_statistics()
        print(f"파일 통계: {stats}")
        
        # 7. 파일 삭제 테스트 (소프트 삭제)
        print("\n=== 파일 삭제 테스트 ===")
        success = db_manager.delete_glb_file(file_id=file_id)
        if success:
            print("파일 삭제 성공")
        else:
            print("파일 삭제 실패")
    
    finally:
        # 데이터베이스 연결 해제
        db_manager.disconnect()

async def test_fastapi_endpoints():
    """FastAPI 엔드포인트 테스트"""
    
    base_url = "http://localhost:28000"
    
    print("=== FastAPI 엔드포인트 테스트 ===")
    
    # 1. 파일 목록 조회
    print("\n1. GLB 파일 목록 조회")
    response = requests.get(f"{base_url}/glb-db/list-glb-db/")
    if response.status_code == 200:
        data = response.json()
        print(f"응답: {data}")
    else:
        print(f"오류: {response.status_code}")
    
    # 2. 파일 통계 조회
    print("\n2. GLB 파일 통계 조회")
    response = requests.get(f"{base_url}/glb-db/stats-db/")
    if response.status_code == 200:
        data = response.json()
        print(f"통계: {data}")
    else:
        print(f"오류: {response.status_code}")
    
    # 3. 파일 검색
    print("\n3. GLB 파일 검색")
    response = requests.get(f"{base_url}/glb-db/search-glb-db/?limit=10")
    if response.status_code == 200:
        data = response.json()
        print(f"검색 결과: {data}")
    else:
        print(f"오류: {response.status_code}")

def create_test_glb_file():
    """테스트용 GLB 파일 생성"""
    
    # 간단한 GLB 파일 구조 (실제로는 유효한 GLB 파일이어야 함)
    glb_header = b"glTF\x02\x00\x00\x00"  # GLB 헤더
    json_chunk = b'{"asset":{"version":"2.0"},"scene":0,"scenes":[{"nodes":[]}],"nodes":[]}'  # JSON 데이터
    json_length = len(json_chunk)
    json_padding = b'\x20' * ((4 - (json_length % 4)) % 4)  # 4바이트 정렬
    json_chunk_full = json_length.to_bytes(4, 'little') + b'JSON' + json_chunk + json_padding
    
    # 바이너리 데이터 (빈 데이터)
    bin_chunk = b''
    bin_length = len(bin_chunk)
    bin_padding = b'\x00' * ((4 - (bin_length % 4)) % 4)  # 4바이트 정렬
    bin_chunk_full = bin_length.to_bytes(4, 'little') + b'BIN\x00' + bin_chunk + bin_padding
    
    # 전체 파일 크기
    total_size = 12 + len(json_chunk_full) + len(bin_chunk_full)
    
    # GLB 파일 생성
    glb_data = glb_header + total_size.to_bytes(4, 'little') + json_chunk_full + bin_chunk_full
    
    return glb_data

if __name__ == "__main__":
    print("GLB 데이터베이스 관리 시스템 테스트")
    print("=" * 50)
    
    # 1. 데이터베이스 작업 테스트
    test_glb_database_operations()
    
    # 2. FastAPI 엔드포인트 테스트
    asyncio.run(test_fastapi_endpoints())
    
    print("\n테스트 완료!") 
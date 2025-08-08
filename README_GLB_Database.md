# GLB 파일 MySQL 저장 시스템

이 시스템은 GLB (GL Binary) 파일을 MySQL 데이터베이스에 저장하고 관리하는 기능을 제공합니다.

## 🗄️ 데이터베이스 스키마

### 주요 테이블

#### 1. `glb_files` - GLB 파일 저장 테이블
```sql
CREATE TABLE glb_files (
    id INT AUTO_INCREMENT PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    file_size BIGINT NOT NULL,
    content_type VARCHAR(100) DEFAULT 'model/gltf-binary',
    file_data LONGBLOB NOT NULL,
    file_hash VARCHAR(64) NOT NULL,
    upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    description TEXT,
    tags JSON,
    created_by VARCHAR(100),
    updated_by VARCHAR(100)
);
```

#### 2. `glb_file_metadata` - 파일 메타데이터 테이블 (선택사항)
```sql
CREATE TABLE glb_file_metadata (
    id INT AUTO_INCREMENT PRIMARY KEY,
    file_id INT NOT NULL,
    metadata_key VARCHAR(100) NOT NULL,
    metadata_value TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (file_id) REFERENCES glb_files(id) ON DELETE CASCADE
);
```

#### 3. `glb_file_access_log` - 파일 접근 로그 테이블 (선택사항)
```sql
CREATE TABLE glb_file_access_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    file_id INT NOT NULL,
    access_type ENUM('download', 'view', 'upload', 'delete') NOT NULL,
    access_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_ip VARCHAR(45),
    user_agent TEXT,
    FOREIGN KEY (file_id) REFERENCES glb_files(id) ON DELETE CASCADE
);
```

## 🚀 주요 기능

### 1. 파일 업로드
```python
from app.core.models.glb_database import GLBDatabaseManager

db_manager = GLBDatabaseManager()
db_manager.connect()

# GLB 파일 저장
file_id = db_manager.save_glb_file(
    filename="model.glb",
    file_data=binary_data,
    description="3D 모델 파일",
    tags=["model", "3d", "game"],
    created_by="admin"
)
```

### 2. 파일 목록 조회
```python
# 모든 파일 목록 조회
files = db_manager.list_glb_files(limit=100, offset=0)

# 페이지네이션
files = db_manager.list_glb_files(limit=10, offset=20)
```

### 3. 파일 다운로드
```python
# 파일 메타데이터 조회
file_info = db_manager.get_glb_file(file_id=1)

# 파일 바이너리 데이터 조회
file_data = db_manager.get_glb_file_data(file_id=1)
```

### 4. 파일 정보 업데이트
```python
success = db_manager.update_glb_file(
    file_id=1,
    description="업데이트된 설명",
    tags=["updated", "model"],
    updated_by="admin"
)
```

### 5. 파일 삭제 (소프트 삭제)
```python
success = db_manager.delete_glb_file(file_id=1)
```

## 🌐 FastAPI 엔드포인트

### 파일 업로드
```bash
curl -X POST "http://localhost:28000/glb-db/upload-glb-db/" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@model.glb" \
  -F "description=3D 모델 파일" \
  -F "tags=[\"model\", \"3d\"]" \
  -F "created_by=admin"
```

### 파일 목록 조회
```bash
curl -X GET "http://localhost:28000/glb-db/list-glb-db/?limit=10&offset=0"
```

### 파일 다운로드
```bash
curl -X GET "http://localhost:28000/glb-db/download-glb-db/1" \
  -H "accept: application/json" \
  -o downloaded_model.glb
```

### 파일 메타데이터 조회
```bash
curl -X GET "http://localhost:28000/glb-db/metadata-db/1"
```

### 파일 정보 업데이트
```bash
curl -X PUT "http://localhost:28000/glb-db/update-glb-db/1" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "업데이트된 설명",
    "tags": "[\"updated\", \"model\"]",
    "updated_by": "admin"
  }'
```

### 파일 삭제
```bash
curl -X DELETE "http://localhost:28000/glb-db/delete-glb-db/1"
```

### 파일 통계 조회
```bash
curl -X GET "http://localhost:28000/glb-db/stats-db/"
```

### 파일 검색
```bash
curl -X GET "http://localhost:28000/glb-db/search-glb-db/?filename=model&limit=10"
```

## 🔧 설정

### 1. 데이터베이스 연결 설정
```python
db_manager = GLBDatabaseManager(
    host='localhost',
    port=3306,
    user='root',
    password='your_password',
    database='db_manager'
)
```

### 2. 테이블 생성
```bash
mysql -u root -p db_manager < database_schema.sql
```

## 📊 성능 최적화

### 1. 인덱스 활용
- `filename` 인덱스로 빠른 파일 검색
- `file_hash` 인덱스로 중복 파일 체크
- `upload_time` 인덱스로 시간 기반 정렬

### 2. 캐싱 전략
- Redis를 활용한 파일 목록 캐싱
- 파일 메타데이터 캐싱
- 파일 바이너리 데이터 캐싱

### 3. 메모리 관리
- LONGBLOB 타입으로 대용량 파일 지원
- 스트리밍 다운로드로 메모리 효율성 확보

## 🔒 보안 기능

### 1. 파일 해시 검증
- SHA256 해시로 파일 무결성 보장
- 중복 파일 자동 감지

### 2. 접근 로그
- 모든 파일 접근 기록
- 다운로드, 조회, 업로드, 삭제 로그

### 3. 소프트 삭제
- 실제 데이터 삭제 대신 `is_active = FALSE`로 표시
- 데이터 복구 가능

## 📈 모니터링

### 1. 파일 통계
- 전체 파일 수
- 전체 파일 크기
- 최근 업로드 파일 수
- 가장 많이 다운로드된 파일

### 2. 성능 메트릭
- 업로드/다운로드 속도
- 캐시 히트율
- 데이터베이스 응답 시간

## 🧪 테스트

### 테스트 실행
```bash
python glb_database_example.py
```

### 테스트 항목
1. 파일 업로드 테스트
2. 파일 목록 조회 테스트
3. 파일 다운로드 테스트
4. 파일 정보 업데이트 테스트
5. 파일 삭제 테스트
6. FastAPI 엔드포인트 테스트

## 🚨 주의사항

1. **대용량 파일 처리**: LONGBLOB 타입은 최대 4GB까지 지원
2. **메모리 사용량**: 대용량 파일 업로드 시 충분한 메모리 확보 필요
3. **데이터베이스 백업**: 정기적인 백업으로 데이터 보호
4. **네트워크 대역폭**: 대용량 파일 전송 시 네트워크 대역폭 고려

## 📝 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 
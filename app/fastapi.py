from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from os.path import dirname, abspath
from pathlib import Path
from datetime import timedelta
import logging
import sys
from datetime import datetime

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from starlette.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware

from app.core.routers import db_route, file_manage

BASE_DIR = dirname(abspath(__file__))
# templates = Jinja2Templates(directory=str(Path(BASE_DIR, 'core/templates')))

# 로깅 설정
def setup_logging():
    # 로그 포맷 설정 (타임라인 포함)
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    
    # 로거 설정
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        datefmt=date_format,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('app.log', encoding='utf-8')
        ]
    )
    
    # uvicorn 로거 설정
    uvicorn_logger = logging.getLogger("uvicorn")
    uvicorn_logger.setLevel(logging.INFO)
    
    # FastAPI 로거 설정
    fastapi_logger = logging.getLogger("fastapi")
    fastapi_logger.setLevel(logging.INFO)
    
    return logging.getLogger(__name__)

# 로깅 설정 적용
logger = setup_logging()

app = FastAPI()

origins = [
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["POST", "GET"],
    allow_headers=["*"],  # 모든 HTTP 헤더 허용
)

# 요청 로깅 미들웨어
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = datetime.now()
    
    # 요청 정보 로깅
    logger.info(f"Request started: {request.method} {request.url}")
    logger.info(f"Client: {request.client.host}:{request.client.port}")
    
    response = await call_next(request)
    
    # 응답 시간 계산 및 로깅
    process_time = datetime.now() - start_time
    logger.info(f"Request completed: {request.method} {request.url} - Status: {response.status_code} - Time: {process_time.total_seconds():.3f}s")
    
    return response

# app.mount("/static", StaticFiles(directory=str(Path(BASE_DIR, 'static'))), name="static")
# app.mount("/glb", StaticFiles(directory=str(Path(BASE_DIR, 'glb'))), name="glb")

app.include_router(db_route.router, prefix="/db", tags=["db"])
app.include_router(file_manage.router, prefix="/file", tags=["file"])
# app.include_router(glb_database_route.router, prefix="/glb-db", tags=["glb-database"])

# 애플리케이션 시작/종료 로깅
@app.on_event("startup")
async def startup_event():
    logger.info("FastAPI application started")
    # DB 연결 풀 초기화 확인
    try:
        from app.core.routers.db_route import db_manager
        if db_manager.health_check():
            logger.info("Database connection pool initialized successfully")
        else:
            logger.error("Database connection pool initialization failed")
    except Exception as e:
        logger.error(f"Failed to initialize database connections: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("FastAPI application shutdown")
    # DB 연결 풀 정리
    try:
        from app.core.routers.db_route import db_manager
        db_manager.close_all_connections()
        logger.info("Database connections closed successfully")
    except Exception as e:
        logger.error(f"Failed to close database connections: {e}")

# 헬스 체크 엔드포인트 추가
@app.get("/health")
async def health_check():
    """애플리케이션 및 데이터베이스 상태 확인"""
    try:
        from app.core.routers.db_route import db_manager, cache_manager
        
        # DB 상태 확인
        db_healthy = db_manager.health_check()
        
        # Redis 상태 확인
        redis_healthy = cache_manager.health_check()
        
        # 전체 상태 결정
        overall_healthy = db_healthy and redis_healthy
        
        return {
            "status": "healthy" if overall_healthy else "unhealthy",
            "database": "connected" if db_healthy else "disconnected",
            "redis": "connected" if redis_healthy else "disconnected",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "database": "error",
            "redis": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/health/detailed")
async def detailed_health_check():
    """상세한 헬스 체크 정보"""
    try:
        from app.core.routers.db_route import db_manager, cache_manager
        
        # DB 상태 확인
        db_healthy = db_manager.health_check()
        
        # Redis 상태 확인
        redis_healthy = cache_manager.health_check()
        redis_stats = cache_manager.get_cache_stats() if redis_healthy else {"error": "Redis not available"}
        
        return {
            "status": "healthy" if (db_healthy and redis_healthy) else "unhealthy",
            "database": {
                "status": "connected" if db_healthy else "disconnected",
                "connection_pool_size": len(db_manager.connection_pool) if hasattr(db_manager, 'connection_pool') else 0
            },
            "redis": {
                "status": "connected" if redis_healthy else "disconnected",
                "stats": redis_stats
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Detailed health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

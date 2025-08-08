import redis
import json
import logging
from typing import Optional, Any, Dict, List
from config import config

logger = logging.getLogger(__name__)

class CacheManager:
    def __init__(self):
        self.redis_host = config.REDIS_HOST
        self.redis_port = config.REDIS_PORT
        self.redis_password = config.REDIS_PASSWORD
        self.connection_timeout = config.REDIS_CONNECTION_TIMEOUT
        self.socket_timeout = config.REDIS_SOCKET_TIMEOUT
        self._redis_client = None
        self._initialize_redis()
    
    def _initialize_redis(self):
        """Redis 연결 초기화"""
        try:
            self._redis_client = redis.StrictRedis(
                host=self.redis_host,
                port=self.redis_port,
                password=self.redis_password,
                decode_responses=True,
                socket_connect_timeout=self.connection_timeout,
                socket_timeout=self.socket_timeout,
                retry_on_timeout=True,
                health_check_interval=config.REDIS_HEALTH_CHECK_INTERVAL
            )
            # 연결 테스트
            self._redis_client.ping()
            logger.info("Redis connection initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Redis connection: {e}")
            self._redis_client = None
    
    def _get_redis_client(self) -> Optional[redis.StrictRedis]:
        """Redis 클라이언트 가져오기 (재연결 포함)"""
        if self._redis_client is None:
            self._initialize_redis()
            return self._redis_client
        
        try:
            # 연결 상태 확인
            self._redis_client.ping()
            return self._redis_client
        except Exception as e:
            logger.warning(f"Redis connection lost, attempting to reconnect: {e}")
            self._initialize_redis()
            return self._redis_client
    
    def make_cache_key(self, table: str, columns: List[str] = None, filters: Dict[str, Any] = None) -> str:
        """
        캐시 키를 생성하는 함수
        table, columns, filters를 모두 포함하여 고유한 키 생성
        """
        key_parts = [table]
        
        # columns 추가
        if columns:
            columns_str = ",".join(sorted(columns))
            key_parts.append(f"cols:{columns_str}")
        else:
            key_parts.append("cols:*")
        
        # filters 추가
        if filters:
            sorted_items = sorted(filters.items())
            filter_values = [f"{k}:{v}" for k, v in sorted_items]
            key_parts.append("filters:" + "|".join(filter_values))
        else:
            key_parts.append("filters:none")
        
        return ":".join(key_parts)

    def get_data_from_cache(self, _table: str, _columns: List[str] = None, _filters: Dict[str, Any] = None) -> Optional[str]:
        """캐시에서 데이터 조회"""
        try:
            redis_client = self._get_redis_client()
            if not redis_client:
                logger.warning("Redis client not available")
                return None
            
            key_data: str = self.make_cache_key(table=_table, columns=_columns, filters=_filters)    
            result = redis_client.get(key_data)
            
            if result:
                logger.debug(f"Cache hit for key: {key_data}")
            else:
                logger.debug(f"Cache miss for key: {key_data}")
            
            return result
        except Exception as e:
            logger.error(f"Failed to get data from cache: {e}")
            return None

    def save_data_to_cache(self, _table: str, _columns: List[str] = None, _filters: Dict[str, Any] = None, db_data: Any = None, ttl: int = None) -> bool:
        """캐시에 데이터를 저장하는 함수

        Args:
            _table (str): 테이블명
            _columns (list): 컬럼 리스트
            _filters (dict): 필터 조건
            db_data (dict): 데이터베이스에서 가져온 데이터
            ttl (int, optional): 캐시의 유효 시간(초). Defaults to config.CACHE_DEFAULT_TTL.
        
        Returns:
            bool: 저장 성공 여부
        """
        if not db_data:
            return False
        
        if ttl is None:
            ttl = config.CACHE_DEFAULT_TTL
        
        try:
            redis_client = self._get_redis_client()
            if not redis_client:
                logger.warning("Redis client not available")
                return False
            
            key = self.make_cache_key(table=_table, columns=_columns, filters=_filters)
            redis_client.setex(key, ttl, json.dumps(db_data))
            logger.debug(f"Data saved to cache with key: {key}, TTL: {ttl}s")
            return True
        except Exception as e:
            logger.error(f"Failed to save data to cache: {e}")
            return False
    
    def clear_cache(self, pattern: str = "*") -> bool:
        """캐시 삭제"""
        try:
            redis_client = self._get_redis_client()
            if not redis_client:
                return False
            
            keys = redis_client.keys(pattern)
            if keys:
                redis_client.delete(*keys)
                logger.info(f"Cleared {len(keys)} cache entries matching pattern: {pattern}")
            return True
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
            return False
    
    def health_check(self) -> bool:
        """Redis 연결 상태 확인"""
        try:
            redis_client = self._get_redis_client()
            if not redis_client:
                return False
            
            redis_client.ping()
            return True
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return False
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """캐시 통계 정보"""
        try:
            redis_client = self._get_redis_client()
            if not redis_client:
                return {"error": "Redis client not available"}
            
            info = redis_client.info()
            return {
                "connected_clients": info.get("connected_clients", 0),
                "used_memory_human": info.get("used_memory_human", "0B"),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0)
            }
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {"error": str(e)}
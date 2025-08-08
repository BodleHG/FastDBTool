import pymysql
import logging
from typing import Optional, List, Dict, Any
from contextlib import contextmanager
import time
from config import config

logger = logging.getLogger(__name__)

class DBManager:
    def __init__(self):
        self.connection_pool = []
        self.max_connections = config.DB_MAX_CONNECTIONS
        self.connection_timeout = config.DB_CONNECTION_TIMEOUT
        self._initialize_connections()
    
    def _initialize_connections(self):
        """연결 풀 초기화"""
        try:
            for _ in range(self.max_connections):
                conn = self._create_connection()
                if conn:
                    self.connection_pool.append(conn)
            logger.info(f"Database connection pool initialized with {len(self.connection_pool)} connections")
        except Exception as e:
            logger.error(f"Failed to initialize connection pool: {e}")
    
    def _create_connection(self) -> Optional[pymysql.Connection]:
        """새로운 DB 연결 생성"""
        try:
            conn = pymysql.connect(
                host=config.DB_HOST,
                port=config.DB_PORT,
                user=config.DB_USER,
                password=config.DB_PASSWORD,
                db=config.DB_NAME,
                charset='utf8',
                cursorclass=pymysql.cursors.DictCursor,
                autocommit=True,
                connect_timeout=self.connection_timeout,
                read_timeout=config.DB_READ_TIMEOUT,
                write_timeout=config.DB_WRITE_TIMEOUT
            )
            return conn
        except Exception as e:
            logger.error(f"Failed to create database connection: {e}")
            return None
    
    def _get_connection(self) -> Optional[pymysql.Connection]:
        """사용 가능한 연결 가져오기"""
        if not self.connection_pool:
            logger.warning("No available connections in pool, creating new connection")
            return self._create_connection()
        
        # 연결 풀에서 연결 가져오기
        conn = self.connection_pool.pop()
        
        # 연결 상태 확인
        if self._is_connection_valid(conn):
            return conn
        else:
            logger.warning("Invalid connection detected, creating new one")
            return self._create_connection()
    
    def _return_connection(self, conn: pymysql.Connection):
        """연결을 풀로 반환"""
        if conn and self._is_connection_valid(conn):
            self.connection_pool.append(conn)
        else:
            logger.warning("Invalid connection not returned to pool")
    
    def _is_connection_valid(self, conn: pymysql.Connection) -> bool:
        """연결이 유효한지 확인"""
        try:
            if conn is None:
                return False
            
            # 연결 상태 확인
            conn.ping(reconnect=False)
            return True
        except Exception as e:
            logger.debug(f"Connection validation failed: {e}")
            return False
    
    @contextmanager
    def _get_cursor(self):
        """커서 컨텍스트 매니저"""
        conn = None
        cursor = None
        try:
            conn = self._get_connection()
            if not conn:
                raise Exception("Failed to get database connection")
            
            cursor = conn.cursor()
            yield cursor
        except Exception as e:
            logger.error(f"Database operation failed: {e}")
            raise
        finally:
            if cursor:
                cursor.close()
            if conn:
                self._return_connection(conn)
    
    def get_data(self, _sql: str) -> List[Dict[str, Any]]:
        """데이터 조회"""
        try:
            with self._get_cursor() as cursor:
                cursor.execute(_sql)
                result = cursor.fetchall()
                return result
        except Exception as e:
            logger.error(f"Failed to execute query: {_sql}, Error: {e}")
            raise
    
    def insert_data(self, _sql: str) -> str:
        """데이터 삽입"""
        try:
            with self._get_cursor() as cursor:
                cursor.execute(_sql)
                return "success"
        except pymysql.MySQLError as e:
            logger.error(f"MySQL error during insert: {e}")
            return f"Error: {str(e)}"
        except Exception as e:
            logger.error(f"Unexpected error during insert: {e}")
            return f"Error: {str(e)}"
    
    def json_to_sql_select(self, _table: str, _columns: List[str] = None, _filters: Dict[str, Any] = None) -> str:
        """JSON을 SQL SELECT 쿼리로 변환"""
        if not _columns:
            columns = "*"
        else:
            columns = ", ".join(_columns)
        
        if not _filters:
            return f"SELECT {columns} FROM {_table};"
        
        conditions = []
        for key, value in _filters.items():
            if isinstance(value, str):
                value = value.replace("'", "''")
                conditions.append(f"{key}='{value}'")
            else:
                conditions.append(f"{key}={value}")
        
        where_clause = " AND ".join(conditions)
        return f"SELECT {columns} FROM {_table} WHERE {where_clause};"
    
    def json_to_sql_insert(self, _table: str, _data: Dict[str, Any]) -> str:
        """JSON을 SQL INSERT 쿼리로 변환"""
        columns = ", ".join(_data.keys())
        values = []
        for value in _data.values():
            if isinstance(value, str):
                value = value.replace("'", "''")  # SQL escape
                values.append(f"'{value}'")
            else:
                values.append(str(value))
        values_str = ", ".join(values)
        return f"INSERT INTO {_table} ({columns}) VALUES ({values_str});"
    
    def json_to_sql_delete(self, _table: str, _filters: Dict[str, Any]) -> str:
        """JSON을 SQL DELETE 쿼리로 변환"""
        if not _filters:
            raise ValueError("DELETE operation requires filters for safety")
        
        conditions = []
        for key, value in _filters.items():
            if isinstance(value, str):
                value = value.replace("'", "''")  # SQL escape
                conditions.append(f"{key}='{value}'")
            else:
                conditions.append(f"{key}={value}")
        
        where_clause = " AND ".join(conditions)
        return f"DELETE FROM {_table} WHERE {where_clause};"
    
    def delete_data(self, _sql: str) -> str:
        """데이터 삭제"""
        try:
            with self._get_cursor() as cursor:
                cursor.execute(_sql)
                affected_rows = cursor.rowcount
                if affected_rows > 0:
                    logger.info(f"Successfully deleted {affected_rows} rows")
                    return f"success: {affected_rows} rows deleted"
                else:
                    logger.warning("No rows were deleted (no matching records)")
                    return "success: no rows deleted (no matching records)"
        except pymysql.MySQLError as e:
            logger.error(f"MySQL error during delete: {e}")
            return f"Error: {str(e)}"
        except Exception as e:
            logger.error(f"Unexpected error during delete: {e}")
            return f"Error: {str(e)}"
    
    def close_all_connections(self):
        """모든 연결 닫기"""
        for conn in self.connection_pool:
            try:
                conn.close()
            except Exception as e:
                logger.error(f"Error closing connection: {e}")
        self.connection_pool.clear()
        logger.info("All database connections closed")
    
    def health_check(self) -> bool:
        """데이터베이스 연결 상태 확인"""
        try:
            with self._get_cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                return result is not None
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
        
    def glb_by_id(self, _id: int, _table: str):
        sql = f"""
        SELECT 
            main_table.name as {_table}_name, 
            main_table.description as {_table}_description, 
            GLB.name as glb_name,
            GLB.description as glb_description,
            GLB.data as glb_data
        FROM {_table} main_table
        INNER JOIN GLB ON main_table.glb_id = GLB.id
        WHERE main_table.id = {_id}
        """
            
        return sql
            
        
        
    
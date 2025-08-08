from fastapi import APIRouter, Depends, Request, responses, status, Response, Body
from typing import Dict, Any
from ..models.database import DBManager 
from ..models.cache import CacheManager
from ..models.base_model import DBSelect, DBInsert, DBDelete
import json
from .response_format import ResponseFormat
import queue
import io
from starlette.responses import StreamingResponse

db_manager = DBManager()
cache_manager = CacheManager()

router = APIRouter()

@router.post("/read/")
async def read(dbquery: DBSelect):    
    try:
        dict_data: dict = dict(dbquery)
        
        table = dict_data["table"]
        columns = dict_data["columns"]
        filters = dict_data["filters"]
        
        result = cache_manager.get_data_from_cache(_table=table, _columns=columns, _filters=filters)
        
        # Return DB Data
        if not result:            
            result = db_manager.get_data(_sql=db_manager.json_to_sql_select(_table=table, _columns=columns, _filters=filters))
            if not result:
                return ResponseFormat.sql_fail("No data found")
            
            cache_manager.save_data_to_cache(_table=table, _columns=columns, _filters=filters, db_data=result)
            # print("Data fetched from DB and saved to cache")
            
            return ResponseFormat.sql_success(result)      

        # Return Cached Data
        # print("Result From Redis")
        return ResponseFormat.sql_success(json.loads(result))
        
    except Exception as e:
        return "Unknown error occurred: " + str(e)

@router.post("/insert/")
async def insert(dbquery: DBInsert):    
    try:
        dict_data: dict = dict(dbquery)
        
        table = dict_data["table"]
        data = dict_data["data"]
        
        result = db_manager.insert_data(_sql=db_manager.json_to_sql_insert(_table=table, _data=data))
        
        # if result == "success":
        #     return ResponseFormat.sql_success(result)
        # else:
        #     return ResponseFormat.sql_fail(result)
        
        return result
        
    except Exception as e:
        return "Unknown error occurred: " + str(e)

@router.post("/delete/")
async def delete(dbquery: DBDelete):    
    try:
        dict_data: dict = dict(dbquery)
        
        table = dict_data["table"]
        filters = dict_data["filters"]
        
        # 안전성을 위해 필터가 비어있는지 확인
        if not filters:
            return ResponseFormat.sql_fail("DELETE operation requires filters for safety")
        
        # DELETE 쿼리 생성 및 실행
        result = db_manager.delete_data(_sql=db_manager.json_to_sql_delete(_table=table, _filters=filters))
        
        # 캐시에서 관련 데이터 삭제
        try:
            cache_manager.clear_cache(pattern=f"{table}:*")
        except Exception as cache_error:
            # 캐시 삭제 실패는 로그만 남기고 계속 진행
            print(f"Cache clear warning: {cache_error}")
        
        # 결과 반환
        if result.startswith("success"):
            return ResponseFormat.sql_success(result)
        else:
            return ResponseFormat.sql_fail(result)
        
    except Exception as e:
        return "Unknown error occurred: " + str(e)    


@router.get("/data-by-glb/")
async def get_data_by_glb(
    id: int,
    table: str
):
    try:
        sql = db_manager.glb_by_id(_id=id, _table=table)
        if not sql:
            return {"error": "SQL 생성에 실패했습니다."}
        result = db_manager.get_data(_sql=sql)
        if not result:
            return {"error": "데이터를 찾을 수 없습니다."}
        return {"data": result}
    except Exception as e:
        return {"error": f"알 수 없는 오류 발생: {str(e)}"}

  
  
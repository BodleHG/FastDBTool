#!/usr/bin/env python3
"""
데이터베이스 및 Redis 연결 상태 모니터링 스크립트
"""

import requests
import time
import logging
from datetime import datetime
import json

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('connection_monitor.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class ConnectionMonitor:
    def __init__(self, base_url: str = "http://localhost:28000"):
        self.base_url = base_url
        self.health_endpoint = f"{base_url}/health"
        self.detailed_health_endpoint = f"{base_url}/health/detailed"
    
    def check_health(self) -> dict:
        """기본 헬스 체크"""
        try:
            response = requests.get(self.health_endpoint, timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Health check failed with status code: {response.status_code}")
                return {"status": "error", "error": f"HTTP {response.status_code}"}
        except requests.exceptions.RequestException as e:
            logger.error(f"Health check request failed: {e}")
            return {"status": "error", "error": str(e)}
    
    def check_detailed_health(self) -> dict:
        """상세 헬스 체크"""
        try:
            response = requests.get(self.detailed_health_endpoint, timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Detailed health check failed with status code: {response.status_code}")
                return {"status": "error", "error": f"HTTP {response.status_code}"}
        except requests.exceptions.RequestException as e:
            logger.error(f"Detailed health check request failed: {e}")
            return {"status": "error", "error": str(e)}
    
    def monitor_connections(self, interval: int = 60, max_failures: int = 3):
        """연결 상태 지속 모니터링"""
        failure_count = 0
        
        logger.info(f"Starting connection monitoring. Checking every {interval} seconds.")
        
        while True:
            try:
                # 기본 헬스 체크
                health_status = self.check_health()
                
                if health_status.get("status") == "healthy":
                    failure_count = 0
                    logger.info("✅ All connections healthy")
                else:
                    failure_count += 1
                    logger.warning(f"❌ Connection issues detected. Failure count: {failure_count}")
                    
                    # 상세 정보 로깅
                    detailed_status = self.check_detailed_health()
                    logger.warning(f"Detailed status: {json.dumps(detailed_status, indent=2)}")
                    
                    if failure_count >= max_failures:
                        logger.error(f"🚨 Maximum failures ({max_failures}) reached. Consider restarting the application.")
                
                # 상세 정보 주기적 로깅 (매 10번째 체크마다)
                if failure_count == 0 and (time.time() // interval) % 10 == 0:
                    detailed_status = self.check_detailed_health()
                    logger.info(f"📊 Detailed status: {json.dumps(detailed_status, indent=2)}")
                
                time.sleep(interval)
                
            except KeyboardInterrupt:
                logger.info("Monitoring stopped by user")
                break
            except Exception as e:
                logger.error(f"Unexpected error during monitoring: {e}")
                time.sleep(interval)

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Database and Redis connection monitor")
    parser.add_argument("--url", default="http://localhost:28000", 
                       help="Base URL of the FastAPI application")
    parser.add_argument("--interval", type=int, default=60,
                       help="Check interval in seconds (default: 60)")
    parser.add_argument("--max-failures", type=int, default=3,
                       help="Maximum consecutive failures before alert (default: 3)")
    
    args = parser.parse_args()
    
    monitor = ConnectionMonitor(args.url)
    
    print(f"Starting connection monitor for {args.url}")
    print(f"Check interval: {args.interval} seconds")
    print(f"Max failures: {args.max_failures}")
    print("Press Ctrl+C to stop monitoring")
    print("-" * 50)
    
    monitor.monitor_connections(args.interval, args.max_failures)

if __name__ == "__main__":
    main() 
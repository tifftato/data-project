# ---------------------------------------
# 작성자: 김서현 (광주 2반, G040)
# 작성목적: [종합 실습1] 데이터 수집 미니 파이프라인
# 작성자: 2026-07-20

# 활용 파일: Python_Practice1_Data.json

# 본 파일은 SKALA 교육을 위한 과제 코드이므로 작성자에게 모든 저작권이 있습니다.
#
# 변경사항 내역 (날짜, 변경목적, 변경내용 순으로 기입)
#
# ----------------------------------------
import asyncio
import time
import logging
import pandas as pd
import httpx
from typing import Tuple
from pydantic import BaseModel, Field, field_validator, ValidationError

# ==========================================
# 1. 로거(Logger) 설정 구역: 파일과 화면에 동시에 기록
# ==========================================
# 에러를 화면뿐만 아니라 'pipeline.log' 파일에도 저장하도록 설정합니다.
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s', # 시간, 위험도, 메시지 순으로 기록
    handlers=[
        logging.FileHandler("pipeline.log", encoding='utf-8'), # 파일로 저장
        logging.StreamHandler()                                # 터미널 화면에 출력
    ]
)
logger = logging.getLogger(__name__)

# ==========================================
# 2. Pydantic 스키마 정의 (기존과 동일)
# ==========================================
class WeatherRecord(BaseModel):
    time: str = Field(...)
    temperature: float = Field(..., ge=-50, le=60)
    precipitation_prob: int = Field(..., ge=0, le=100)

class CountryRecord(BaseModel):
    name: str = Field(..., description="국가명")
    area: float = Field(...,ge=0)
    population: float = Field(...,ge=0)
    latlng: Tuple[float, float] = Field(..., description="[위도, 경도] 리스트")
    @field_validator('latlng')
    @classmethod
    def validate_latlng_range(cls, value):
        lat, lng = value 
        if not (-90 <= lat <= 90):
            raise ValueError(f"위도(lat)는 -90~90 사이여야 합니다. (입력값: {lat})")
        if not (-180 <= lng <= 180):
            raise ValueError(f"경도(lng)는 -180~180 사이여야 합니다. (입력값: {lng})")
        return value
    

class IpRecord(BaseModel):
    query: str = Field(...)
    status: str = Field(...)
    country: str = Field(...)
    lat: float = Field(...)
    lon: float = Field(...)

# ==========================================
# 3. 디테일한 예외 처리가 추가된 수집 함수
# ==========================================
async def fetch_api(client: httpx.AsyncClient, url: str, api_name: str) -> dict:
    """단일 API를 비동기로 호출하고 상세한 예외 처리를 수행합니다."""
    try:
        response = await client.get(url)
        response.raise_for_status() 
        logger.info(f"[{api_name}] 수집 성공")
        return response.json()
        
    # 예외 1: HTTP 상태 코드 에러 (예: 404 Not Found, 500 Server Error)
    except httpx.HTTPStatusError as e:
        logger.error(f"[{api_name}] 서버 응답 에러 (상태코드: {e.response.status_code}): {url}")
        return {}
        
    # 예외 2: 네트워크 연결 에러 (인터넷 끊김, 타임아웃 등)
    except httpx.RequestError:
        logger.error(f"[{api_name}] 네트워크 요청 실패: {url}")
        return {}
        
    # 예외 3: 그 외 전혀 예상치 못한 에러 (이때는 Traceback을 남깁니다)
    except Exception:
        # exc_info=True를 주면 에러가 발생한 코드의 위치까지 상세히 로그에 남습니다.
        logger.error(f"[{api_name}] 알 수 없는 치명적 오류 발생", exc_info=True)
        return {}

# ==========================================
# 4. 데이터 파이프라인 메인 비동기 함수
# ==========================================
async def main():
    urls = {
        "Weather": "https://api.open-meteo.com/v1/forecast?latitude=37.5665&longitude=126.9780&hourly=temperature_2m,precipitation_probability&forecast_days=3&timezone=Asia/Seoul",
        "Country": "https://countries.dev/alpha/KOR",
        "IP": "http://ip-api.com/json/8.8.8.8"
    }

    async with httpx.AsyncClient() as client:
        tasks = [
            fetch_api(client, urls["Weather"], "Weather"),
            fetch_api(client, urls["Country"], "Country"),
            fetch_api(client, urls["IP"], "IP")
        ]
        weather_raw, country_raw, ip_raw = await asyncio.gather(*tasks)

    valid_weather_data = []
    
    logger.info("--- 데이터 스키마 검증 시작 ---")
    
    # 1) 날씨 데이터 검증
    if weather_raw and "hourly" in weather_raw:
        hourly = weather_raw["hourly"]
        for t, temp, prob in zip(hourly["time"], hourly["temperature_2m"], hourly["precipitation_probability"]):
            try:
                weather_record = WeatherRecord(time=t, temperature=temp, precipitation_prob=prob)
                valid_weather_data.append(weather_record.model_dump())
            except ValidationError as e:
                logger.warning(f"[검증 경고 - Weather] 데이터 오류 (시간: {t}) - 사유: {e.errors()[0]['msg']}")
        logger.info(f"[검증 완료 - Weather] 총 {len(valid_weather_data)}건 정상 검증")

    # 2) 나라 데이터 검증
    try: 
        if country_raw:
            country_record = CountryRecord(**country_raw)
            logger.info(f"[검증 성공 - Country] {country_record.name} 위치: {country_record.latlng}")
    except ValidationError as e:
        # 불필요한 (시간: {t}) 제거
        logger.error(f"[검증 실패 - Country] 데이터 또는 범위 오류 - 사유: {e.errors()[0]['msg']}")

    # 3) IP 데이터 검증
    try:
        if ip_raw:
            ip_record = IpRecord(**ip_raw)
            logger.info(f"[검증 성공 - IP] {ip_record.query} -> {ip_record.country}")
    except ValidationError as e:
        # 불필요한 (시간: {t}) 제거
        logger.error(f"[검증 실패 - IP] 데이터 구조 변경 의심 - 사유: {e.errors()[0]['msg']}")

    # ------------------------------------------
    # 저장 매체 성능 비교 및 최종 저장 (중복 제거)
    # ------------------------------------------
    print("\n--- 저장 형식 성능 비교 (CSV vs Parquet) ---")
    df = pd.DataFrame(valid_weather_data)
    
    if not df.empty:
        try:
            # [CSV 쓰기 성능 측정]
            start_time = time.time()
            df.to_csv("weather_data.csv", index=False)
            csv_write_time = time.time() - start_time
            
            # [Parquet 쓰기 성능 측정]
            start_time = time.time()
            df.to_parquet("weather_data.parquet", engine="pyarrow", index=False)
            parquet_write_time = time.time() - start_time

            # [CSV 읽기 성능 측정]
            start_time = time.time()
            pd.read_csv("weather_data.csv")
            csv_read_time = time.time() - start_time

            # [Parquet 읽기 성능 측정]
            start_time = time.time()
            pd.read_parquet("weather_data.parquet", engine="pyarrow")
            parquet_read_time = time.time() - start_time

            # 결과 출력
            print(f"데이터 건수: {len(df)}건")
            print(f"[쓰기] CSV: {csv_write_time:.6f}초 | Parquet: {parquet_write_time:.6f}초")
            print(f"[읽기] CSV: {csv_read_time:.6f}초 | Parquet: {parquet_read_time:.6f}초")
            
            if parquet_write_time < csv_write_time and parquet_read_time < csv_read_time:
                print("💡 결론: Parquet 형식이 쓰기와 읽기 모두에서 더 빠른 성능을 보였습니다.")
            else:
                print("💡 데이터 크기가 작아 성능 차이가 미미할 수 있습니다.")
                
            logger.info("✅ 데이터 성능 측정 및 저장 완료 (CSV, Parquet)")
            
        except Exception:
            logger.error("파일 저장 중 오류가 발생했습니다.", exc_info=True)
    else:
        logger.warning("검증을 통과한 날씨 데이터가 없어 성능 테스트와 저장을 건너뜁니다.")


if __name__ == "__main__":
    print("✅ 프로그램 진입 성공!") # <--- 이 줄을 추가해 보세요!
    import sys
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())

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
import pytest
from pydantic import ValidationError
from pipeline import WeatherRecord

def test_weather_record_valid():
    """정상 데이터가 Pydantic 모델을 무사히 통과하는지 테스트합니다."""
    # 정상 데이터 모형
    valid_data = {
        "time": "2024-01-01T12:00",
        "temperature": 15.5,
        "precipitation_prob": 30
    }
    
    # 에러 없이 객체가 생성되어야 함
    weather_record = WeatherRecord(**valid_data)
    assert weather_record.temperature == 15.5
    assert weather_record.precipitation_prob == 30

def test_weather_record_invalid_temperature():
    """온도 범위(ge=-50, le=60)를 벗어난 데이터가 에러를 발생시키는지 테스트합니다."""
    invalid_data = {
        "time": "2024-01-01T12:00",
        "temperature": 100.0, # 상한선(60) 초과 에러 유발
        "precipitation_prob": 30
    }
    
    # ValidationError가 발생하는지 확인
    with pytest.raises(ValidationError):
        WeatherRecord(**invalid_data)

def test_weather_record_invalid_prob():
    """강수 확률 범위(0~100)를 벗어난 데이터가 에러를 발생시키는지 테스트합니다."""
    invalid_data = {
        "time": "2024-01-01T12:00",
        "temperature": 15.0,
        "precipitation_prob": -10 # 하한선(0) 미달 에러 유발
    }
    
    with pytest.raises(ValidationError):
        WeatherRecord(**invalid_data)

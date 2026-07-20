import pytest
from pydantic import ValidationError
from pipeline import WeatherRecord, CountryRecord, IpRecord

# ==========================================
# 1. WeatherRecord (날씨 데이터) 테스트
# ==========================================
def test_weather_valid():
    """[정상] 모든 조건이 완벽한 날씨 데이터"""
    data = {"time": "2026-07-20T12:00", "temperature": 25.5, "precipitation_prob": 50}
    record = WeatherRecord(**data)
    assert record.temperature == 25.5

def test_weather_invalid_temp_high():
    """[오류] 온도 상한선(60도) 초과"""
    data = {"time": "2026-07-20T12:00", "temperature": 60.1, "precipitation_prob": 50}
    with pytest.raises(ValidationError):
        WeatherRecord(**data)

def test_weather_invalid_temp_low():
    """[오류] 온도 하한선(-50도) 미달"""
    data = {"time": "2026-07-20T12:00", "temperature": -50.1, "precipitation_prob": 50}
    with pytest.raises(ValidationError):
        WeatherRecord(**data)

def test_weather_invalid_prob_high():
    """[오류] 강수 확률 상한선(100%) 초과"""
    data = {"time": "2026-07-20T12:00", "temperature": 20.0, "precipitation_prob": 101}
    with pytest.raises(ValidationError):
        WeatherRecord(**data)

def test_weather_invalid_prob_low():
    """[오류] 강수 확률 하한선(0%) 미달"""
    data = {"time": "2026-07-20T12:00", "temperature": 20.0, "precipitation_prob": -1}
    with pytest.raises(ValidationError):
        WeatherRecord(**data)

def test_weather_missing_field():
    """[오류] 필수 항목(time) 누락"""
    data = {"temperature": 20.0, "precipitation_prob": 50}
    with pytest.raises(ValidationError):
        WeatherRecord(**data)


# ==========================================
# 2. CountryRecord (국가 데이터) 테스트
# ==========================================
def test_country_valid():
    """[정상] 모든 조건이 완벽한 국가 데이터"""
    data = {
        "name": "South Korea", 
        "area": 100210.0, 
        "population": 51000000.0, 
        "latlng": [37.5665, 126.9780]
    }
    record = CountryRecord(**data)
    assert record.name == "South Korea"

def test_country_invalid_area_negative():
    """[오류] 면적(area)이 음수인 경우 (ge=0 조건 위배)"""
    data = {"name": "Test", "area": -10.0, "population": 1000.0, "latlng": [0.0, 0.0]}
    with pytest.raises(ValidationError):
        CountryRecord(**data)

def test_country_invalid_population_negative():
    """[오류] 인구(population)가 음수인 경우 (ge=0 조건 위배)"""
    data = {"name": "Test", "area": 100.0, "population": -5.0, "latlng": [0.0, 0.0]}
    with pytest.raises(ValidationError):
        CountryRecord(**data)

def test_country_invalid_latlng_length():
    """[오류] 위경도 리스트의 개수가 2개가 아닌 경우"""
    # 숫자가 3개 들어간 경우
    data = {"name": "Test", "area": 100.0, "population": 1000.0, "latlng": [37.5, 126.9, 10.0]}
    with pytest.raises(ValidationError):
        CountryRecord(**data)

def test_country_invalid_lat_range():
    """[오류] 위도(lat)가 -90 ~ 90 범위를 벗어난 경우"""
    data = {"name": "Test", "area": 100.0, "population": 1000.0, "latlng": [90.1, 126.9]}
    with pytest.raises(ValidationError):
        CountryRecord(**data)

def test_country_invalid_lng_range():
    """[오류] 경도(lng)가 -180 ~ 180 범위를 벗어난 경우"""
    data = {"name": "Test", "area": 100.0, "population": 1000.0, "latlng": [37.5, -180.1]}
    with pytest.raises(ValidationError):
        CountryRecord(**data)


# ==========================================
# 3. IpRecord (IP 데이터) 테스트
# ==========================================
def test_ip_valid():
    """[정상] 모든 조건이 완벽한 IP 데이터"""
    data = {
        "query": "8.8.8.8", 
        "status": "success", 
        "country": "United States", 
        "lat": 39.03, 
        "lon": -77.5
    }
    record = IpRecord(**data)
    assert record.query == "8.8.8.8"

def test_ip_missing_fields():
    """[오류] 필수 항목 일부 누락"""
    data = {
        "query": "8.8.8.8", 
        "status": "success"
        # country, lat, lon 누락
    }
    with pytest.raises(ValidationError):
        IpRecord(**data)

def test_ip_invalid_type():
    """[오류] 숫자(float)가 들어가야 할 곳에 문자가 들어간 경우"""
    data = {
        "query": "8.8.8.8", 
        "status": "success", 
        "country": "United States", 
        "lat": "알수없음", # float 변환 불가
        "lon": -77.5
    }
    with pytest.raises(ValidationError):
        IpRecord(**data)
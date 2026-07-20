# ---------------------------------------
# 작성자: 김서현 (광주 2반, G040)
# 작성목적: [실습2] 파일 I/O, 예외 처리, Pydantic 검증 파이프라인 실습 목적 코드
# 작성자: 2026-07-20

# 활용 파일: Python_Practice1_Data.json

# 본 파일은 SKALA 교육을 위한 과제 코드이므로 작성자에게 모든 저작권이 있습니다.
#
# 변경사항 내역 (날짜, 변경목적, 변경내용 순으로 기입)
#
# ----------------------------------------

import pydantic
import csv
import json
import logging
from typing import Optional
from pydantic import BaseModel, Field, ValidationError

# ==========================================
# 0. 로거 설정 
# ==========================================
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# ==========================================
# 1. Pydantic v2 스키마 정의
# ==========================================
class SalesRecord(BaseModel):
    month: str = Field(..., min_length=1, description="날짜 (비어있으면 안됨)")
    region: str = Field(..., min_length=1, description="지역 (비어있으면 안됨)")
    amount: int = Field(..., gt=0, description="매출액 (0 초과)")
    category: Optional[str] = None

# ==========================================
# 2. 예외 처리 + 만능 파일 읽기 함수 (CSV & JSON)
# ==========================================
def safe_load_file(file_path: str):
    data = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            # 1) CSV 파일일 경우
            if file_path.endswith('.csv'):
                reader = csv.DictReader(f)
                for row in reader:
                    data.append(row)
            
            # 2) JSON 파일일 경우
            elif file_path.endswith('.json'):
                content = f.read()
                # 이전 실습의 특수한 JSON 형태(sales = )를 위한 전처리
                json_str = content.replace('sales = ', '').replace('sales=', '').strip()
                data = json.loads(json_str)
            
            # 3) 지원하지 않는 파일일 경우
            else:
                logger.error(f"[{file_path}] 지원하지 않는 확장자입니다.")
                return None
                
        logger.info(f"[{file_path}] 파일에서 {len(data)}건의 데이터를 성공적으로 불러왔습니다.")
        return data
        
    except FileNotFoundError:
        logger.error(f"[{file_path}] 파일을 찾을 수 없습니다.")
        return None
    except Exception as e:
        logger.error(f"[{file_path}] 파일 읽기 중 알 수 없는 오류 발생: {e}")
        return None
    finally:
        print(f"==> [{file_path}] 로딩 종료")

# ==========================================
# 3. 데이터 검증 및 저장 함수
# ==========================================
def process_and_save_data(raw_data, output_name):
    if raw_data is None:
        return
        
    valid_records = []
    error_records = []

    for row in raw_data:
        try:
            record = SalesRecord(**row)
            valid_records.append(record)
        except ValidationError as e:
            # 오류 출력
            print(f"⚠️ 검증 오류 데이터: {row}")
            print(f"   오류 상세: {e.errors()[0]['msg']}") 
            error_records.append({"row": row, "error": str(e)})

    print(f"[{output_name}] 검증 완료: 정상 {len(valid_records)}건, 오류 {len(error_records)}건")

    # 정상 레코드 CSV 저장
    if valid_records:
        valid_csv_path = f'valid_{output_name}.csv'
        with open(valid_csv_path, 'w', encoding='utf-8', newline='') as f:
            fieldnames = valid_records[0].model_fields.keys()
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for record in valid_records:
                writer.writerow(record.model_dump()) 
    
    # 오류 레코드 JSON 저장
    if error_records:
        error_json_path = f'errors_{output_name}.json'
        with open(error_json_path, 'w', encoding='utf-8') as f:
            json.dump(error_records, f, ensure_ascii=False, indent=4) 
            
    return valid_records, error_records

# ==========================================
# 4. 전체 파이프라인 실행
# ==========================================
def run_pipeline():
    print("\n================ [1단계: 기존 CSV 테스트] ================")
    # Checkpoint: 없는 파일 예외 처리 테스트
    assert safe_load_file('ghost_file.csv') is None
    
    # 테스트용 CSV 만들기
    test_csv_path = 'raw_data.csv'
    test_data = [
        {"month": "2024-01", "region": "서울", "amount": 1500, "category": "전자"}, 
        {"month": "2024-01", "region": "부산", "amount": 800, "category": "의류"},  
        {"month": "2024-02", "region": "대구", "amount": 950, "category": ""},      
        {"month": "2024-02", "region": "광주", "amount": 2100},                     
        {"month": "2024-03", "region": "", "amount": 1000, "category": "전자"},     
        {"month": "2024-03", "region": "제주", "amount": -500, "category": "식품"}, 
        {"month": "", "region": "서울", "amount": 0, "category": "식품"},                     
    ]
    with open(test_csv_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["region", "category", "amount", "month"])
        writer.writeheader()
        writer.writerows(test_data)

    csv_data = safe_load_file(test_csv_path)
    valid_csv, error_csv = process_and_save_data(csv_data, "test_csv")
    
    # Checkpoint 통과 확인
    assert len(valid_csv) == 4
    assert len(error_csv) == 3
    reloaded_data = safe_load_file('valid_test_csv.csv')
    assert len(reloaded_data) == len(valid_csv)


    print("\n================ [2단계: 실전 JSON 파일 테스트] ================")
    json_file_path = 'Python_Practice1_Data.json'
    json_data = safe_load_file(json_file_path)
    
    if json_data:
        process_and_save_data(json_data, "practice_json")
    else:
        print(f"⚠️ {json_file_path} 파일을 찾을 수 없어 JSON 테스트를 건너뜁니다.")
        
    print("\n 파이프라인 실행 완료")

if __name__ == "__main__":
    run_pipeline()
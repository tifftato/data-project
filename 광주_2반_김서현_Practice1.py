# ---------------------------------------
# 작성자: 김서현 (광주 2반, G040)
# 작성목적: [실습1] 자료구조 집계, 컴프리헨션, 제너레이션 실습 목적 코드
# 작성자: 2026-07-20

# 활용 파일: Python_Practice1_Data.json

# 본 파일은 SKALA 교육을 위한 sample 코드이므로 작성자에게 모든 저작권이 있습니다.
#
# 변경사항 내역 (날짜, 변경목적, 변경내용 순으로 기입)
#
# ----------------------------------------
import json
import sys
from collections import defaultdict, Counter

# 데이터 불러오기

with open("Python_Practice1_Data.json", "r", encoding="utf-8") as f:
    # Practice1 파일은 순수한 json이 아니므로 파일 전체를 문자열로 read
    content = f.read()

    # "sales = " 부분을 찾아서 빈칸으로 만든 뒤 json으로 변환
    json_str = content.replace("sales = ", "")
    sales = json.loads(json_str)

# [1] amount >= 1000 만 필터링
filtered_sales = [item for item in sales if item["amount"] >= 1000]

# [1] 지역별 총매출 dict를 컴프리헨션으로 계산
region_total = {
    r: sum(item["amount"] for item in sales if item["region"] == r)
    for r in {i["region"] for i in sales}
}
print("지역별 총매출: ", region_total)


# [2] counter로 지역별 거래 건수 및 most_common 확인
region_counts = Counter(item["region"] for item in sales)
print("지역 별 거래 건수: ", region_counts)
print("가장 거래가 많은 지역 순서: ", region_counts.most_common())  # Checkpoint 반영

# [2] defaultdict로 카테고리별 amount 리스트
category_amounts = defaultdict(list)
for item in sales:
    category_amounts[item["category"]].append(item["amount"])
print("카테고리별 amount 리스트: ", dict(category_amounts))


# [3] 제너레이터 - 메모리 비교
list_ver = [item for item in sales if item["amount"] > 1000]
gen_ver = (item for item in sales if item["amount"] > 1000)

print(f"리스트 크기: {sys.getsizeof(list_ver)} bytes")
print(
    f"제너레이터 크기: {sys.getsizeof(gen_ver)} bytes"
)  # 제너레이터를 list()로 변환하지 마세요!


# [4] 종합 - 월별 카테고리 매출 집계
grouped_data = defaultdict(int)
for item in sales:
    key = (item["month"], item["category"])
    grouped_data[key] += item["amount"]

# [4] Top 3 금액 내림차순 정렬
sorted_top3 = sorted(grouped_data.items(), key=lambda x: x[1], reverse=True)[:3]
print("매출 상위 3개 항목: ", sorted_top3)

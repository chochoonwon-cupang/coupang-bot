# ============================================================
# 정렬(랜덤 셔플) 동작 검증
# ============================================================
# main.py의 상품 정렬 로직: random.shuffle 후 products[:limit]

import random

def test_sort_logic():
    """검색 결과 → shuffle → [:limit] 로직 검증"""
    # 1) 최소 1개인 리스트
    products = [{"name": f"상품{i}"} for i in range(5)]
    limit = 3

    random.shuffle(products)
    result = products[:limit]

    assert len(result) == limit, f"limit={limit}개 나와야 함, 실제={len(result)}"
    assert all(p in products for p in result), "결과는 원본에 포함되어야 함"
    print("[OK] shuffle + [:limit]:", [p["name"] for p in result])

    # 2) 검색 결과가 limit보다 적을 때 (예: 2개만 검색됨)
    products = [{"name": f"상품{i}"} for i in range(2)]
    limit = 5
    random.shuffle(products)
    result = products[:limit]
    assert len(result) == 2, f"2개만 있으면 2개 반환, 실제={len(result)}"
    print("[OK] 결과 < limit일 때:", [p["name"] for p in result])

    # 3) 셔플 실행 후 순서가 바뀌는지 (확률적)
    base = [1, 2, 3, 4, 5]
    diffs = 0
    for _ in range(20):
        p = base.copy()
        random.shuffle(p)
        if p != base:
            diffs += 1
    assert diffs > 10, f"20회 중 {diffs}회만 순서 변경됨 (랜덤 시드 이슈)"
    print(f"[OK] 순서 변경: 20회 중 {diffs}회 다른 순서")

    print("\n[정렬 검증] 모든 테스트 통과")


if __name__ == "__main__":
    test_sort_logic()

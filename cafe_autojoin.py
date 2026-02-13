# ============================================================
# 도우미 카페 자동 가입 모듈
# ============================================================
# 서버(helper_cafes)에서 카페리스트를 불러와 자동 가입
# 포스팅도우미(posting_help) 로직 참고
# ============================================================

import time
import base64
import requests

# Selenium 지연 로드
By = None
EC = None
WebDriverWait = None
TimeoutException = None


def _ensure_selenium():
    global By, EC, WebDriverWait, TimeoutException
    if By is not None:
        return
    from selenium.webdriver.common.by import By as _By
    from selenium.webdriver.support import expected_conditions as _EC
    from selenium.webdriver.support.ui import WebDriverWait as _WDW
    from selenium.common.exceptions import TimeoutException as _TE
    By = _By
    EC = _EC
    WebDriverWait = _WDW
    TimeoutException = _TE


def _solve_captcha(captcha_image_url, api_key, log=None):
    """2captcha API로 캡챠 해독"""
    _log = log or print
    if not api_key or not api_key.strip():
        return None
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://cafe.naver.com/",
            "Accept": "image/webp,image/apng,image/*,*/*;q=0.8",
        }
        img_resp = requests.get(captcha_image_url, headers=headers, timeout=10)
        img_resp.raise_for_status()
        image_data = img_resp.content
        if len(image_data) == 0:
            return None
        image_base64 = base64.b64encode(image_data).decode("utf-8")

        in_url = "https://2captcha.com/in.php"
        params = {"key": api_key.strip(), "method": "base64", "body": image_base64}
        resp = requests.post(in_url, data=params, timeout=30)
        if resp.status_code != 200:
            return None
        result = resp.text.strip()
        if not result.startswith("OK|"):
            _log(f"[캡챠 API] Task 생성 실패: {result}")
            return None
        task_id = result.split("|")[1]

        res_url = "https://2captcha.com/res.php"
        max_wait = 120
        wait_time = 0
        while wait_time < max_wait:
            time.sleep(5)
            wait_time += 5
            params = {"key": api_key.strip(), "action": "get", "id": task_id}
            resp = requests.get(res_url, params=params, timeout=10)
            if resp.status_code != 200:
                continue
            result = resp.text.strip()
            if result.startswith("OK|"):
                text = result.split("|")[1]
                _log(f"[캡챠 API] 해독 성공: {text}")
                return text
            if result == "CAPCHA_NOT_READY":
                continue
            _log(f"[캡챠 API] 해독 실패: {result}")
            return None
        return None
    except Exception as e:
        _log(f"[캡챠 API] 오류: {e}")
        return None


def _try_join_one(driver, idx, cafe_name, cafe_url, cafe_id, menu_id, captcha_api_key, log):
    """한 카페에 가입 시도. 성공 시 dict 반환, 실패 시 None."""
    _log = log or print
    _ensure_selenium()
    try:
        _log(f"[도우미 가입] [{idx}] {cafe_name} - 이동 중: {cafe_url[:50]}...")
        driver.get(cafe_url)
        time.sleep(3)

        # 가입 버튼 찾기
        join_btn = None
        for sel in [
            "div.cafe-write-btn a._rosRestrict[onclick*='joinCafe']",
            "a._rosRestrict[onclick*='joinCafe']",
        ]:
            try:
                join_btn = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, sel))
                )
                break
            except Exception:
                continue

        if not join_btn:
            try:
                write_btn = driver.find_element(By.CSS_SELECTOR, "div.cafe-write-btn a")
                onclick = write_btn.get_attribute("onclick") or ""
                if "writeBoard(" in onclick:
                    _log(f"[도우미 가입] [{idx}] {cafe_name} - 이미 멤버")
                    return {"cafe_id": cafe_id, "menu_id": menu_id}
            except Exception:
                pass
            _log(f"[도우미 가입] [{idx}] {cafe_name} - 가입 버튼 없음")
            return None

        driver.execute_script(
            "arguments[0].scrollIntoView({behavior:'smooth',block:'center'});", join_btn
        )
        time.sleep(0.5)
        join_btn.click()
        time.sleep(2)

        # 캡챠 처리
        try:
            captcha_img = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "img.image[alt='캡차이미지']")
                )
            )
            captcha_url = captcha_img.get_attribute("src")
            if captcha_url:
                text = _solve_captcha(captcha_url, captcha_api_key, log)
                if text:
                    inp = WebDriverWait(driver, 3).until(
                        EC.presence_of_element_located(
                            (By.CSS_SELECTOR, "input#captcha.input_text")
                        )
                    )
                    inp.clear()
                    inp.send_keys(text)
                    time.sleep(1)
                    confirm_btn = WebDriverWait(driver, 3).until(
                        EC.element_to_be_clickable(
                            (By.CSS_SELECTOR, "div.join_btn a.BaseButton--skinGreen")
                        )
                    )
                    confirm_btn.click()
                    time.sleep(2)
        except TimeoutException:
            pass
        except Exception as e:
            _log(f"[도우미 가입] [{idx}] {cafe_name} - 캡챠 처리 오류: {e}")
            return None

        _log(f"[도우미 가입] [{idx}] {cafe_name} - 가입 완료")
        return {"cafe_id": cafe_id, "menu_id": menu_id}
    except Exception as e:
        _log(f"[도우미 가입] [{idx}] {cafe_name} - 오류: {e}")
        return None


def run_helper_cafe_join(
    naver_id,
    naver_pw,
    helper_cafes,
    captcha_api_key,
    log=None,
    stop_flag=None,
    driver_holder=None,
    on_progress=None,
    on_joined=None,
):
    """
    도우미 카페 리스트로 자동 가입 수행.

    Args:
        naver_id: 네이버 아이디
        naver_pw: 네이버 비밀번호
        helper_cafes: [{"cafe_url", "cafe_id", "menu_id"}, ...]
        captcha_api_key: 2captcha API 키
        log: 로그 콜백
        stop_flag: 중지 여부 확인 함수 (callable, True 반환 시 중지)
        driver_holder: {"driver": ...} 드라이버 저장
        on_progress: (pct, text) 진행률 콜백
        on_joined: (joined_list) 가입 완료 시 콜백
    """
    _log = log or print
    driver_holder = driver_holder or {}
    stop_flag = stop_flag or (lambda: False)

    from cafe_poster import setup_driver, login_to_naver, safe_quit_driver

    driver = None
    joined = []
    total = len(helper_cafes)

    try:
        _log("[도우미 가입] 크롬 드라이버 설정 중...")
        driver = setup_driver(headless=False)
        driver_holder["driver"] = driver

        if stop_flag():
            return
        _log("[도우미 가입] 네이버 로그인 중...")
        if not login_to_naver(driver, naver_id, naver_pw, log=_log):
            _log("[도우미 가입] 로그인 실패")
            return
        time.sleep(2)

        for i, c in enumerate(helper_cafes):
            if stop_flag():
                _log("[도우미 가입] 중지됨")
                break
            pct = int((i / total) * 100)
            if on_progress:
                on_progress(pct, f"가입 중 ({i+1}/{total})")
            cafe_name = c.get("cafe_url", "")[:30] + "..."
            result = _try_join_one(
                driver, i + 1, cafe_name,
                c.get("cafe_url", ""), c.get("cafe_id", ""), c.get("menu_id", ""),
                captcha_api_key, _log
            )
            if result:
                joined.append(result)
            time.sleep(2)

        if on_progress:
            on_progress(100, "완료")
        if on_joined and joined:
            on_joined(joined)
        _log(f"[도우미 가입] 완료: {len(joined)}개 가입 성공")
    except Exception as e:
        _log(f"[도우미 가입] 오류: {e}")
    finally:
        safe_quit_driver(driver)
        driver_holder["driver"] = None

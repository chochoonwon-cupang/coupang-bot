# ============================================================
# 네이버 카페 자동 포스팅 모듈 (Selenium)
# ============================================================
# pyperclip을 이용한 복사-붙여넣기 로그인 방식으로
# 네이버 캡차 우회, 카페 글쓰기 자동화
# ============================================================

import time
import random
import os
import re
import tempfile

# Selenium / pyperclip은 실제 포스팅 시에만 필요하므로 지연 import 사용
# (GUI에서 load_cafe_list만 호출할 때 ModuleNotFoundError 방지)
pyperclip = None
webdriver = None
By = None
Keys = None
ActionChains = None
WebDriverWait = None
EC = None
Service = None
Options = None
TimeoutException = None
ChromeDriverManager = None


def _ensure_selenium():
    """Selenium 및 pyperclip을 지연 로드합니다."""
    global pyperclip, webdriver, By, Keys, ActionChains
    global WebDriverWait, EC, Service, Options, TimeoutException, ChromeDriverManager

    if webdriver is not None:
        return  # 이미 로드됨

    try:
        import pyperclip as _pyperclip
        pyperclip = _pyperclip
    except ImportError:
        raise ImportError(
            "pyperclip 패키지가 필요합니다.\n"
            "설치: pip install pyperclip"
        )

    try:
        from selenium import webdriver as _wd
        from selenium.webdriver.common.by import By as _By
        from selenium.webdriver.common.keys import Keys as _Keys
        from selenium.webdriver.common.action_chains import ActionChains as _AC
        from selenium.webdriver.support.ui import WebDriverWait as _WDW
        from selenium.webdriver.support import expected_conditions as _EC
        from selenium.webdriver.chrome.service import Service as _Svc
        from selenium.webdriver.chrome.options import Options as _Opt
        from selenium.common.exceptions import TimeoutException as _TE
        from webdriver_manager.chrome import ChromeDriverManager as _CDM

        webdriver = _wd
        By = _By
        Keys = _Keys
        ActionChains = _AC
        WebDriverWait = _WDW
        EC = _EC
        Service = _Svc
        Options = _Opt
        TimeoutException = _TE
        ChromeDriverManager = _CDM
    except ImportError:
        raise ImportError(
            "selenium / webdriver-manager 패키지가 필요합니다.\n"
            "설치: pip install selenium webdriver-manager"
        )

# ── 상수 ──
LOGIN_URL = "https://nid.naver.com/nidlogin.login"


# ─────────────────────────────────────────────────────────────
# 1. 크롬 드라이버 설정
# ─────────────────────────────────────────────────────────────
def setup_driver(headless=False):
    """
    Chrome WebDriver를 설정하고 반환합니다.
    webdriver-manager로 자동으로 크롬 드라이버를 다운로드/관리합니다.
    """
    _ensure_selenium()
    chrome_options = Options()

    if headless:
        chrome_options.add_argument("--headless=new")

    # 자동화 감지 방지
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)

    # 일반 옵션
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1280,900")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--lang=ko_KR")
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    # 알림 차단
    prefs = {"profile.default_content_setting_values.notifications": 2}
    chrome_options.add_experimental_option("prefs", prefs)

    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
    except Exception:
        # webdriver-manager 실패 시 로컬 chromedriver 사용 시도
        driver = webdriver.Chrome(options=chrome_options)

    # 자동화 감지 우회
    driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {"source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"},
    )
    return driver


# ─────────────────────────────────────────────────────────────
# 2. 네이버 로그인 (pyperclip 복사-붙여넣기)
# ─────────────────────────────────────────────────────────────
def login_to_naver(driver, naver_id, naver_pw, log=None):
    """
    pyperclip을 이용한 복사-붙여넣기 방식으로 네이버 로그인.
    캡차를 피하기 위해 send_keys 대신 클립보드 붙여넣기를 사용합니다.

    Returns:
        bool: 로그인 성공 여부
    """
    _ensure_selenium()
    _log = log or print

    if not naver_id or not naver_pw:
        _log("[오류] 네이버 아이디와 비밀번호가 필요합니다.")
        return False

    _log("[로그인] 네이버 로그인 페이지로 이동 중...")
    driver.get(LOGIN_URL)
    time.sleep(2)

    try:
        # 아이디 입력 (pyperclip 복사-붙여넣기)
        _log("[로그인] 아이디 입력 중...")
        id_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "id"))
        )
        id_input.click()
        time.sleep(0.5)

        pyperclip.copy(naver_id)
        time.sleep(0.3)
        id_input.send_keys(Keys.CONTROL, "v")
        time.sleep(0.5)

        # 비밀번호 입력 (pyperclip 복사-붙여넣기)
        _log("[로그인] 비밀번호 입력 중...")
        pw_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "pw"))
        )
        pw_input.click()
        time.sleep(0.5)

        pyperclip.copy(naver_pw)
        time.sleep(0.3)
        pw_input.send_keys(Keys.CONTROL, "v")
        time.sleep(0.5)

        # 로그인 버튼 클릭
        _log("[로그인] 로그인 버튼 클릭...")
        login_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "log.login"))
        )
        login_button.click()

        time.sleep(3)

        # 로그인 성공 확인 (네이버 메인 또는 보안 페이지로 이동)
        current_url = driver.current_url
        if "nidlogin" in current_url:
            _log("[로그인] ⚠ 로그인에 실패했을 수 있습니다. 캡차 또는 2차 인증을 확인하세요.")
            # 수동 해결을 위해 30초 대기
            _log("[로그인] 30초 동안 수동 로그인 대기...")
            time.sleep(30)

        _log("[로그인] ✔ 로그인 완료!")
        return True

    except Exception as e:
        _log(f"[로그인] ✘ 로그인 중 오류 발생: {e}")
        return False


# ─────────────────────────────────────────────────────────────
# 3. 카페 글쓰기 페이지 이동 + 제목/본문 입력
# ─────────────────────────────────────────────────────────────
def type_slowly(driver, text, delay=0.03):
    """ActionChains를 사용해 한 글자씩 타이핑 (자동화 감지 방지)"""
    _ensure_selenium()
    for ch in text:
        ActionChains(driver).send_keys(ch).perform()
        time.sleep(delay)


def _exec_editor_command(driver, cmd, value=None):
    """
    네이버 스마트에디터에 execCommand 적용 (폰트 크기, 굵게, 색상).
    SmartEditor2 호환: fontSize(1-7), bold, foreColor.
    """
    try:
        if value is not None:
            driver.execute_script(
                f"document.execCommand('{cmd}', false, '{value}');"
            )
        else:
            driver.execute_script(
                f"document.execCommand('{cmd}', false, null);"
            )
        time.sleep(0.05)
    except Exception:
        pass


def _type_with_format(driver, text, is_subtitle=False, is_highlight=False, delay=0.02):
    """포맷 적용 후 텍스트 입력. is_subtitle=16pt굵게, is_highlight=파란색"""
    _ensure_selenium()
    if is_subtitle:
        _exec_editor_command(driver, "fontSize", "5")  # ~18pt
        _exec_editor_command(driver, "bold")
    elif is_highlight:
        _exec_editor_command(driver, "foreColor", "#0000FF")

    type_slowly(driver, text, delay=delay)

    if is_subtitle:
        _exec_editor_command(driver, "fontSize", "3")  # 기본 ~14pt
        _exec_editor_command(driver, "bold")
    elif is_highlight:
        _exec_editor_command(driver, "foreColor", "#000000")


def _prepare_image_with_border_and_keyword(img_path, keyword, accent_color=None, log=None):
    """
    이미지에 테두리(20px)를 추가하고, 하단에 키워드 텍스트를
    불투명 배경 위에 가운데 정렬로 삽입합니다. (원본색상 유지)
    accent_color: (r,g,b) — None이면 등록마다 랜덤. 배경·테두리 동일 색상.
    Returns: 수정된 이미지 경로 (실패 시 원본 경로)
    """
    _log = log or print
    if not keyword or not os.path.isfile(img_path):
        return img_path
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        _log("[이미지] Pillow 미설치 — 테두리/키워드 적용 건너뜀")
        return img_path

    try:
        img = Image.open(img_path).convert("RGBA")
        w, h = img.size

        # 1) 테두리 20px
        BORDER = 20

        # 2) 배경·테두리 색상 — 등록마다 랜덤 (흰 글자 대비 어두운 색)
        if accent_color is None:
            r = random.randint(40, 120)
            g = random.randint(40, 120)
            b = random.randint(40, 120)
            accent_color = (r, g, b)
        border_color = (*accent_color, 255)

        # 3) 하단 키워드 영역 — 원본색상 유지 (투명 없음, 불투명 배경)
        font_size = max(14, min(w, h) // 22)
        text_height = font_size + 20
        overlay_color = (*accent_color, 255)  # 불투명

        new_h = h + BORDER * 2 + text_height
        new_w = w + BORDER * 2
        out = Image.new("RGBA", (new_w, new_h), (255, 255, 255, 255))

        draw = ImageDraw.Draw(out)

        # 테두리 (배경색과 동일)
        draw.rectangle([0, 0, new_w - 1, new_h - 1], outline=border_color, width=BORDER)

        # 원본 이미지 붙여넣기 (원본색상 유지)
        out.paste(img, (BORDER, BORDER))

        # 하단 텍스트 영역 — 불투명 배경 (테두리·배경 동일 색상)
        overlay_top = BORDER + h
        draw.rectangle(
            [BORDER, overlay_top, new_w - BORDER - 1, new_h - BORDER - 1],
            fill=overlay_color,
        )

        # 키워드 텍스트 — 흰색, 가운데 정렬
        font = None
        font_paths = [
            "C:/Windows/Fonts/malgun.ttf",
            "C:/Windows/Fonts/gulim.ttc",
            "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
        ]
        for fp in font_paths:
            if os.path.isfile(fp):
                try:
                    font = ImageFont.truetype(fp, font_size)
                    break
                except Exception:
                    pass
        if font is None:
            font = ImageFont.load_default()

        bbox = draw.textbbox((0, 0), keyword, font=font)
        text_w = bbox[2] - bbox[0]
        text_x = BORDER + (new_w - BORDER * 2 - text_w) // 2
        text_y = overlay_top + (text_height - font_size) // 2
        draw.text((text_x, text_y), keyword, fill=(255, 255, 255, 255), font=font)

        out_rgb = out.convert("RGB")

        fd, out_path = tempfile.mkstemp(suffix=".jpg", prefix="cafe_img_")
        os.close(fd)
        out_rgb.save(out_path, "JPEG", quality=92)
        _log(f"[이미지] 테두리+키워드 적용: {os.path.basename(img_path)} → {keyword[:20]}...")
        return out_path
    except Exception as e:
        _log(f"[이미지] 테두리/키워드 적용 실패 (원본 사용): {e}")
        return img_path


def _set_open_settings_public(driver, log=None):
    """
    카페 글쓰기 페이지에서 공개설정을 '전체공개'로 설정합니다.
    참고 HTML: btn_open_set(공개 설정) → radio#all(전체공개)
    """
    _log = log or print
    try:
        # 1) 공개 설정 버튼 클릭 (패널 열기)
        open_btn_selectors = [
            "button.btn_open_set",
            ".open_set button.btn_open_set",
            "button[class*='open_set']",
        ]
        opened = False
        for sel in open_btn_selectors:
            try:
                btn = driver.find_element(By.CSS_SELECTOR, sel)
                if "공개 설정" in (btn.text or ""):
                    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
                    time.sleep(0.3)
                    btn.click()
                    opened = True
                    _log("[포스팅] 공개 설정 패널 열기")
                    break
            except Exception:
                continue
        if not opened:
            # 텍스트로 버튼 찾기
            try:
                btns = driver.find_elements(By.CSS_SELECTOR, "button, .btn_open_set")
                for b in btns:
                    if "공개 설정" in (b.text or ""):
                        b.click()
                        opened = True
                        _log("[포스팅] 공개 설정 패널 열기")
                        break
            except Exception:
                pass
        if not opened:
            _log("[포스팅] 공개 설정 버튼을 찾지 못함 (건너뜀)")
            return

        time.sleep(0.5)

        # 2) 전체공개 라디오 선택 (label 클릭이 가장 안정적)
        try:
            label = driver.find_element(By.CSS_SELECTOR, "label[for='all']")
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", label)
            time.sleep(0.2)
            label.click()
            _log("[포스팅] 전체공개 선택 완료")
            return
        except Exception:
            pass
        try:
            labels = driver.find_elements(By.CSS_SELECTOR, "label.label")
            for lbl in labels:
                if "전체공개" in (lbl.text or ""):
                    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", lbl)
                    time.sleep(0.2)
                    lbl.click()
                    _log("[포스팅] 전체공개 선택 완료 (label)")
                    return
        except Exception:
            pass
        try:
            radio = driver.find_element(By.CSS_SELECTOR, "input#all, input[name='public'][value='true']")
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", radio)
            time.sleep(0.2)
            driver.execute_script("arguments[0].click();", radio)
            _log("[포스팅] 전체공개 선택 완료 (radio)")
            return
        except Exception:
            pass
        _log("[포스팅] 전체공개 라디오를 찾지 못함 (건너뜀)")
    except Exception as e:
        _log(f"[포스팅] 공개설정 설정 중 오류 (건너뜀): {e}")


def write_cafe_post(driver, cafe_id, menu_id, title, body,
                    image_paths=None, image_map=None, keyword=None, log=None):
    """
    네이버 카페에 글을 작성합니다.
    본문 중 '📸 [상품 이미지]' 마커를 만나면
    해당 상품의 다운로드된 이미지를 그 위치에 업로드합니다.
    keyword가 있으면 이미지에 테두리+키워드 텍스트(하단, 배경 투명도 20%)를 적용합니다.

    Args:
        driver: Selenium WebDriver 인스턴스
        cafe_id: 카페 고유 번호
        menu_id: 메뉴(게시판) 번호
        title: 게시글 제목
        body: 게시글 본문
        image_paths: 첨부할 이미지 경로 리스트 (선택, 하위 호환)
        image_map: 순서대로 삽입할 이미지 경로 리스트
                   [img1_path, img2_path, ...] — 본문의 📸 마커 순서와 1:1 매칭
        keyword: 전달 키워드 (이미지 하단에 표시, 테두리 적용)
        log: 로그 콜백 함수

    Returns:
        bool: 성공 여부
    """
    _log = log or print

    # image_map이 없으면 image_paths 리스트를 그대로 사용
    ordered_images = list(image_map or image_paths or [])
    temp_paths = []  # 테두리/키워드 적용 시 생성된 임시 파일 (정리용)
    # 등록마다 랜덤 배경·테두리 색상 (한 포스트 내 이미지들은 동일 색상)
    accent_color = (random.randint(40, 120), random.randint(40, 120), random.randint(40, 120)) if keyword else None
    image_idx = 0  # 다음에 삽입할 이미지 인덱스

    IMAGE_MARKER = "📸 [상품 이미지]"
    import re as _re
    BOLD_PATTERN = _re.compile(r'^\*\*(.+?)\*\*$')
    SUBTITLE_PREFIX = "✅ "
    HIGHLIGHT_PATTERN = _re.compile(r'\[C\](.*?)\[/C\]', _re.DOTALL)

    # 글쓰기 페이지로 직접 이동
    write_url = (
        f"https://cafe.naver.com/ca-fe/cafes/{cafe_id}/menus/{menu_id}"
        f"/articles/write?boardType=L"
    )
    _log(f"[포스팅] 글쓰기 페이지 이동: 카페={cafe_id}, 메뉴={menu_id}")
    driver.get(write_url)
    time.sleep(3)

    # 회원이 아닐 때 표시되는 안내 감지
    try:
        body_text = driver.find_element(By.TAG_NAME, "body").text
        if "회원이 아닙니다" in body_text or "회원이 아니" in body_text or "가입해 주세요" in body_text:
            _log(f"[포스팅] ✘ 이 카페의 회원이 아닙니다. 먼저 카페에 가입해주세요. (cafe_id={cafe_id})")
            return False
    except Exception:
        pass

    try:
        # ── 제목 입력 ──
        _log("[포스팅] 제목 입력 중...")
        title_element = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "textarea.textarea_input"))
        )
        title_element.clear()
        time.sleep(0.3)
        title_element.click()
        time.sleep(0.3)

        # 제목에서 [제목] 태그 제거
        clean_title = title.replace("[제목]", "").replace("[제목]\n", "").strip()
        if len(clean_title) > 100:
            clean_title = clean_title[:97] + "..."

        type_slowly(driver, clean_title, delay=0.03)
        _log(f"[포스팅] 제목 입력 완료: {clean_title[:50]}...")
        time.sleep(1)

        # ── 본문 입력 (이미지 인라인 삽입 포함) ──
        _log("[포스팅] 본문 입력 중...")

        # 본문 영역 클릭 (포커스)
        body_section = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, ".se-section-text, .se-module-text, div.editor_body")
            )
        )
        body_section.click()
        time.sleep(0.5)

        # 본문에서 [본문] 태그 제거
        clean_body = body.replace("[본문]", "").replace("[본문]\n", "").strip()

        # 본문을 줄 단위로 입력
        lines = clean_body.split("\n")
        for i, line in enumerate(lines):
            stripped = line.strip()

            # ── 📸 마커 감지 → 해당 상품 이미지 업로드 (첫 번째 이미지만 테두리+키워드) ──
            if IMAGE_MARKER in stripped and image_idx < len(ordered_images):
                img_path = ordered_images[image_idx]
                if keyword and image_idx == 0:
                    prepared = _prepare_image_with_border_and_keyword(
                        img_path, keyword, accent_color=accent_color, log=_log
                    )
                    if prepared != img_path:
                        temp_paths.append(prepared)
                        img_path = prepared
                _log(f"[포스팅] 📸 상품 {image_idx + 1} 이미지 삽입: "
                     f"{os.path.basename(str(img_path))}")
                _upload_single_image(driver, img_path, _log, click_last_section=True)
                image_idx += 1
                time.sleep(0.6)  # 이미지 섹션 DOM 업데이트 대기
                ActionChains(driver).send_keys(Keys.ENTER).perform()
                time.sleep(0.3)

            # ── **굵은글씨** 마커 감지 → Ctrl+B 토글 ──
            elif BOLD_PATTERN.match(stripped):
                bold_text = BOLD_PATTERN.match(stripped).group(1)
                # 굵게 ON
                ActionChains(driver).key_down(Keys.CONTROL).send_keys('b').key_up(Keys.CONTROL).perform()
                time.sleep(0.1)
                type_slowly(driver, bold_text, delay=0.02)
                # 굵게 OFF
                ActionChains(driver).key_down(Keys.CONTROL).send_keys('b').key_up(Keys.CONTROL).perform()
                time.sleep(0.1)
                if i < len(lines) - 1:
                    ActionChains(driver).send_keys(Keys.ENTER).perform()
                    time.sleep(0.05)

            elif stripped.startswith(SUBTITLE_PREFIX):
                _type_with_format(driver, stripped, is_subtitle=True, delay=0.02)
                if i < len(lines) - 1:
                    ActionChains(driver).send_keys(Keys.ENTER).perform()
                    time.sleep(0.05)

            elif stripped:
                parts = HIGHLIGHT_PATTERN.split(stripped)
                if len(parts) > 1:
                    for seg_idx, seg in enumerate(parts):
                        if seg:
                            is_highlight = (seg_idx % 2 == 1)
                            _type_with_format(driver, seg, is_highlight=is_highlight, delay=0.02)
                else:
                    type_slowly(driver, stripped, delay=0.02)
                if i < len(lines) - 1:
                    ActionChains(driver).send_keys(Keys.ENTER).perform()
                    time.sleep(0.05)
            else:
                # 빈 줄 → Enter만
                if i < len(lines) - 1:
                    ActionChains(driver).send_keys(Keys.ENTER).perform()
                    time.sleep(0.05)

        _log(f"[포스팅] 본문 입력 완료 ({len(clean_body)}자, 이미지 {image_idx}개)")
        time.sleep(1)

        # ── 공개설정: 전체공개 선택 ──
        _set_open_settings_public(driver, _log)
        time.sleep(0.5)

        # ── 등록 버튼 클릭 ──
        _log("[포스팅] 등록 버튼 클릭 중...")
        time.sleep(1)

        # 등록 버튼 찾기 (여러 셀렉터 시도)
        submit_selectors = [
            "button.btn_register",
            "button.BaseButton.ExceedButton",
            "a.btn_submit",
            "button[data-action='submit']",
        ]

        submitted = False
        for selector in submit_selectors:
            try:
                submit_btn = driver.find_element(By.CSS_SELECTOR, selector)
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", submit_btn)
                time.sleep(0.3)
                submit_btn.click()
                submitted = True
                _log("[포스팅] ✔ 등록 버튼 클릭 성공")
                break
            except Exception:
                continue

        if not submitted:
            # JavaScript로 직접 등록 시도
            try:
                driver.execute_script(
                    """
                    var btns = document.querySelectorAll('button, a');
                    for (var b of btns) {
                        var txt = b.textContent.trim();
                        if (txt === '등록' || txt === '발행' || txt === '작성완료') {
                            b.click();
                            break;
                        }
                    }
                    """
                )
                submitted = True
            except Exception as e:
                _log(f"[포스팅] ✘ 등록 버튼 찾기 실패: {e}")

        if submitted:
            time.sleep(3)
            _log("[포스팅] ✔ 포스팅 완료!")
            return True
        else:
            _log("[포스팅] ✘ 등록 버튼을 찾을 수 없습니다.")
            return False

    except Exception as e:
        _log(f"[포스팅] ✘ 글 작성 중 오류: {e}")
        return False
    finally:
        for p in temp_paths:
            try:
                if os.path.isfile(p):
                    os.remove(p)
            except Exception:
                pass


# ─────────────────────────────────────────────────────────────
# 4. 댓글 작성 (포스팅 완료 후 구매 링크 댓글 등록)
#    posting_help.py write_cafe_comment() 참고
#    핵심: cafe_main iframe 전환 → textarea.comment_inbox_text
#         → type_slowly 입력 → a.button.btn_register 클릭
#         → default_content 복귀
# ─────────────────────────────────────────────────────────────
def write_comment(driver, products, log=None):
    """
    포스팅 완료 후 게시글 페이지에서 댓글을 작성합니다.
    네이버 카페는 게시글이 cafe_main iframe 안에 있으므로
    iframe 전환 후 댓글 입력란을 찾습니다.

    댓글 내용 형식:
        ▶ 제품명 1
        구매링크 1

        ▶ 제품명 2
        구매링크 2

    Args:
        driver: Selenium WebDriver (포스팅 완료 후 게시글 페이지)
        products: 상품 정보 리스트 (short_url 포함)
        log: 로그 콜백 함수

    Returns:
        bool: 댓글 작성 성공 여부
    """
    _ensure_selenium()
    _log = log or print

    try:
        _log("[댓글] 댓글 작성 준비 중...")
        time.sleep(3)

        # ── 댓글 본문 구성 ──
        comment_lines = []
        for i, p in enumerate(products):
            name = p.get("productName", "상품")
            link = p.get("short_url", p.get("productUrl", ""))
            if not link:
                continue
            if i > 0:
                comment_lines.append("")  # 상품 사이 빈 줄
            short_name = name if len(name) <= 40 else name[:37] + "..."
            comment_lines.append(f"▶ {short_name}")
            comment_lines.append(link)

        if not comment_lines:
            _log("[댓글] ✘ 링크가 있는 상품이 없습니다.")
            return False

        comment_text = "\n".join(comment_lines)
        product_count = sum(1 for l in comment_lines if l.startswith("▶"))
        _log(f"[댓글] 댓글 내용 구성 완료 (상품 {product_count}개)")

        # ── 1) 최상위 컨텍스트로 전환 ──
        try:
            driver.switch_to.default_content()
        except Exception as e:
            _log(f"[댓글] default_content 전환 오류(무시): {e}")

        # ── 2) cafe_main iframe으로 전환 ──
        try:
            WebDriverWait(driver, 10).until(
                EC.frame_to_be_available_and_switch_to_it((By.ID, "cafe_main"))
            )
        except Exception as e:
            _log(f"[댓글] iframe 'cafe_main' 전환 실패 (현재 컨텍스트에서 시도): {e}")

        # ── 3) 댓글 입력창 찾기 ──
        try:
            comment_box = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "textarea.comment_inbox_text")
                )
            )
        except Exception:
            _log("[댓글] textarea.comment_inbox_text 미발견, 대체 셀렉터 시도...")
            comment_box = None
            fallback_selectors = [
                "textarea.comment_inbox",
                "textarea[placeholder*='댓글']",
                ".comment_writer textarea",
            ]
            for sel in fallback_selectors:
                try:
                    comment_box = WebDriverWait(driver, 3).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, sel))
                    )
                    break
                except Exception:
                    continue

            if not comment_box:
                _log("[댓글] ✘ 댓글 입력란을 찾을 수 없습니다.")
                driver.switch_to.default_content()
                return False

        # ── 4) 댓글 입력 (type_slowly 방식) ──
        try:
            comment_box.click()
            time.sleep(0.3)
            _log("[댓글] 댓글 입력 중...")
            type_slowly(driver, comment_text, delay=0.03)
        except Exception as e:
            _log(f"[댓글] type_slowly 실패, send_keys 시도: {e}")
            try:
                comment_box.send_keys(comment_text)
            except Exception as e2:
                _log(f"[댓글] ✘ 댓글 입력 실패: {e2}")
                driver.switch_to.default_content()
                return False

        time.sleep(0.5)
        _log("[댓글] 댓글 내용 입력 완료")

        # ── 5) 등록 버튼 클릭 ──
        try:
            register_btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR,
                     "a.button.btn_register, button.button.btn_register")
                )
            )
            register_btn.click()
            time.sleep(1.5)
            _log("[댓글] ✔ 댓글 등록 완료!")
            result = True
        except Exception as e:
            _log(f"[댓글] ✘ 댓글 등록 버튼 클릭 실패: {e}")
            result = False

        # ── 6) 최상위 컨텍스트로 복귀 ──
        try:
            driver.switch_to.default_content()
        except Exception:
            pass

        return result

    except Exception as e:
        _log(f"[댓글] ✘ 댓글 작성 중 오류: {e}")
        # 안전하게 최상위 컨텍스트로 복귀
        try:
            driver.switch_to.default_content()
        except Exception:
            pass
        return False


def _find_upload_input(driver):
    """네이버 에디터에서 이미지 업로드용 input[type=file]을 찾는다."""
    selectors = [
        'input[type="file"][accept^="image"]',
        'input[type="file"][accept*="image"]',
        'input[type="file"].se-file-input',
        'input[type="file"]',
    ]
    for css in selectors:
        try:
            elems = driver.find_elements(By.CSS_SELECTOR, css)
            if elems:
                return elems[0]
        except Exception:
            continue
    return None


def _click_photo_toolbar(driver):
    """네이버 에디터 툴바의 사진 버튼을 JavaScript로 클릭한다."""
    script = """
    const cand = [
      'button[aria-label="사진"]',
      'button[aria-label="사진 추가"]',
      'button[aria-label="이미지"]',
      'button[data-name="image"]',
      'button[data-click-area*="photo"]',
      '.se-toolbar-button-photo button',
      '.se-toolbar-item-button-photo button'
    ];
    for (const sel of cand) {
      const b = document.querySelector(sel);
      if (b) { b.click(); return true; }
    }
    return false;
    """
    try:
        return driver.execute_script(script)
    except Exception:
        return False


def _upload_single_image(driver, image_path, log, click_last_section=False):
    """
    posting_help.py 방식으로 이미지 1장을 네이버 에디터에 업로드한다.
    1) input[type=file]을 먼저 찾는다.
    2) 없으면 사진 툴바 버튼을 클릭해서 input을 생성시킨다.
    3) send_keys로 파일 경로를 전송한다.
    click_last_section: True면 마지막 섹션(이미지 포함)을 클릭해 커서를 맨 아래로 둠 (블로그용)
    """
    abs_path = os.path.abspath(image_path)
    if not os.path.isfile(abs_path):
        log(f"[이미지] 파일 없음: {abs_path}")
        return False

    log(f"[이미지] 업로드 시도: {os.path.basename(abs_path)}")

    # 1차: 이미 존재하는 input[type=file] 탐색
    upload_input = _find_upload_input(driver)

    # 2차: 없으면 사진 툴바 버튼 클릭 → input 생성 대기
    if upload_input is None:
        clicked = _click_photo_toolbar(driver)
        if clicked:
            log("[이미지] 사진 버튼 클릭 → 파일 입력 대기...")
            try:
                upload_input = WebDriverWait(driver, 5).until(
                    lambda d: _find_upload_input(d)
                )
            except Exception:
                upload_input = _find_upload_input(driver)

    if upload_input is None:
        log("[이미지] ⚠ 업로드용 input[type=file]을 찾지 못했습니다.")
        return False

    # 3차: send_keys로 파일 업로드
    try:
        upload_input.send_keys(abs_path)
        log(f"[이미지] ✔ 업로드 완료: {os.path.basename(abs_path)}")
        time.sleep(3)  # 업로드 완료 대기
        # 이미지 등록창 닫기 (ESC 후 본문 영역 클릭)
        try:
            ActionChains(driver).send_keys(Keys.ESCAPE).perform()
            time.sleep(0.2)
            if click_last_section:
                sel = ".se-section-text, .se-module-text, .se-module-image, .se-component.se-image, div.editor_body"
                body_els = driver.find_elements(By.CSS_SELECTOR, sel)
                body_el = body_els[-1] if body_els else None
            else:
                body_el = driver.find_element(
                    By.CSS_SELECTOR, ".se-section-text, .se-module-text, div.editor_body"
                )
            if body_el:
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", body_el)
                time.sleep(0.2)
                body_el.click()
                time.sleep(0.2)
        except Exception:
            pass
        return True
    except Exception as e:
        log(f"[이미지] ✘ 업로드 실패: {e}")
        return False


def _add_link_to_last_image(driver, url, log):
    """
    네이버 SmartEditor에서 마지막으로 삽입된 이미지를 클릭(선택) →
    **상단 프로퍼티 툴바**(.se-property-toolbar)의 링크 버튼 클릭 →
    링크 입력 레이어에 URL 입력 → 확인.

    네이버 에디터 구조 참고:
      .se-toolbar-item-link
        button.se-link-toolbar-button[data-name="text-link"]
    """
    _log = log or print
    try:
        # ── 1) 마지막 이미지 컴포넌트 & img 찾기 ──
        comps = driver.find_elements(
            By.CSS_SELECTOR,
            'div.se-component.se-image, div[data-type="image"].se-component')
        if not comps:
            _log("[링크] ⚠ 이미지 컴포넌트를 찾을 수 없습니다.")
            return False

        last_comp = comps[-1]
        try:
            inner_img = last_comp.find_element(
                By.CSS_SELECTOR, 'img.se-image-resource, img')
        except Exception:
            inner_img = last_comp

        # ── 2) 이미지 클릭 (선택) ──
        driver.execute_script(
            "arguments[0].scrollIntoView({block:'center'});", last_comp)
        time.sleep(0.5)

        # 방법 A: ActionChains 실제 마우스 클릭
        ActionChains(driver).move_to_element(inner_img) \
            .pause(0.3).click().perform()
        _log("[링크] 이미지 클릭 (ActionChains)")
        time.sleep(1.0)

        # 방법 B: JS dispatchEvent 보강
        driver.execute_script("""
            var el = arguments[0];
            var rect = el.getBoundingClientRect();
            var cx = rect.left + rect.width / 2;
            var cy = rect.top + rect.height / 2;
            ['mousedown', 'mouseup', 'click'].forEach(function(t) {
                el.dispatchEvent(new MouseEvent(t, {
                    bubbles: true, cancelable: true, view: window,
                    clientX: cx, clientY: cy
                }));
            });
        """, inner_img)
        _log("[링크] 이미지 클릭 (JS dispatchEvent)")
        time.sleep(1.0)

        # ── 3) 상단 프로퍼티 툴바의 링크 버튼 클릭 ──
        # 실제 에디터 HTML 구조:
        #   .se-toolbar-item-link button.se-link-toolbar-button[data-name="text-link"]
        link_btn = None
        link_btn_selectors = [
            'button.se-link-toolbar-button',
            '.se-toolbar-item-link button',
            'button[data-name="text-link"]',
            '.se-property-toolbar button.se-link-toolbar-button',
        ]

        for attempt in range(6):
            for sel in link_btn_selectors:
                btns = driver.find_elements(By.CSS_SELECTOR, sel)
                for btn in btns:
                    try:
                        if btn.is_displayed():
                            link_btn = btn
                            break
                    except Exception:
                        continue
                if link_btn:
                    break
            if link_btn:
                break
            time.sleep(0.5)

        if not link_btn:
            _log("[링크] ⚠ 상단 툴바에서 링크 버튼을 찾을 수 없습니다.")
            return False

        # 링크 버튼 클릭 → 링크 입력 레이어가 열림
        ActionChains(driver).move_to_element(link_btn) \
            .pause(0.2).click().perform()
        _log("[링크] 상단 툴바 링크 버튼 클릭")
        time.sleep(1.5)

        # ── 4) 링크 커스텀 레이어 진단 & 입력 필드 탐색 ──
        input_field = None

        # 4-A) 커스텀 레이어 내부 모든 input 찾기 (진단 로그 포함)
        for attempt in range(10):
            all_inputs = driver.find_elements(By.CSS_SELECTOR, 'input')
            visible_inputs = []
            for inp in all_inputs:
                try:
                    if inp.is_displayed():
                        tag = inp.tag_name
                        itype = inp.get_attribute('type') or ''
                        cls = inp.get_attribute('class') or ''
                        ph = inp.get_attribute('placeholder') or ''
                        visible_inputs.append({
                            'el': inp, 'type': itype,
                            'class': cls, 'placeholder': ph})
                except Exception:
                    continue
            if visible_inputs:
                if attempt == 0:
                    for vi in visible_inputs:
                        _log(f"[링크진단] input type={vi['type']}, "
                             f"class={vi['class'][:60]}, "
                             f"placeholder={vi['placeholder'][:40]}")
                # URL 입력 필드 선택 (placeholder/class 기반)
                for vi in visible_inputs:
                    c = vi['class'].lower()
                    p = vi['placeholder'].lower()
                    if ('link' in c or 'url' in c or 'link' in p
                            or 'url' in p or '링크' in p or '주소' in p
                            or '링크' in vi['placeholder']):
                        input_field = vi['el']
                        break
                # 못 찾으면 마지막 visible text input
                if not input_field:
                    for vi in visible_inputs:
                        if vi['type'] in ('text', 'url', ''):
                            input_field = vi['el']
                if input_field:
                    break
            time.sleep(0.5)

        if not input_field:
            _log("[링크] ⚠ 링크 입력 필드를 찾을 수 없습니다 — URL 텍스트 입력 방지")
            try:
                ActionChains(driver).send_keys(Keys.ESCAPE).perform()
            except Exception:
                pass
            return False

        in_cls = input_field.get_attribute('class') or ''
        in_ph = input_field.get_attribute('placeholder') or ''
        _log(f"[링크] 입력 필드 선택: class={in_cls[:50]}, placeholder={in_ph[:30]}")

        # ── 5) URL 입력 (send_keys 우선 — 가장 안정적) ──
        _log(f"[링크] 입력할 URL (전체): {url}")
        _log(f"[링크] URL 길이: {len(url)}자")

        def _verify():
            """입력 필드에 URL이 제대로 들어갔는지 확인"""
            v = driver.execute_script(
                "return arguments[0].value;", input_field) or ''
            return v.strip(), len(v.strip()) >= len(url) - 2

        # 방법 1: 클릭 → 전체선택 → 클립보드 붙여넣기 (가장 안정적)
        input_field.click()
        time.sleep(0.3)
        # 기존 내용 지우기
        ActionChains(driver).key_down(Keys.CONTROL).send_keys('a') \
            .key_up(Keys.CONTROL).perform()
        time.sleep(0.1)
        pyperclip.copy(url)
        time.sleep(0.1)
        ActionChains(driver).key_down(Keys.CONTROL).send_keys('v') \
            .key_up(Keys.CONTROL).perform()
        time.sleep(0.5)

        val, ok = _verify()
        if ok:
            _log(f"[링크] ✔ 방법1(클립보드) 성공 — 값: {val}")
        else:
            _log(f"[링크] 방법1 실패 (값: {val[:60]}) → 방법2(send_keys) 시도")
            # 방법 2: 직접 타이핑
            input_field.click()
            time.sleep(0.2)
            ActionChains(driver).key_down(Keys.CONTROL).send_keys('a') \
                .key_up(Keys.CONTROL).perform()
            time.sleep(0.1)
            input_field.send_keys(url)
            time.sleep(0.5)
            val, ok = _verify()
            if ok:
                _log(f"[링크] ✔ 방법2(send_keys) 성공 — 값: {val}")

        if not ok:
            _log(f"[링크] 방법2 실패 → 방법3(JS setter + React) 시도")
            # 방법 3: JavaScript value 직접 설정 + React 호환
            driver.execute_script("""
                var input = arguments[0];
                var url   = arguments[1];
                input.focus();
                var tracker = input._valueTracker;
                if (tracker) { tracker.setValue(''); }
                var setter = Object.getOwnPropertyDescriptor(
                    window.HTMLInputElement.prototype, 'value').set;
                setter.call(input, url);
                input.dispatchEvent(new Event('focus',  {bubbles: true}));
                input.dispatchEvent(new Event('input',  {bubbles: true}));
                input.dispatchEvent(new Event('change', {bubbles: true}));
                input.dispatchEvent(new KeyboardEvent('keyup', {bubbles: true, key: 'a'}));
            """, input_field, url)
            time.sleep(0.5)
            val, ok = _verify()
            if ok:
                _log(f"[링크] ✔ 방법3(JS setter) 성공 — 값: {val}")

        if not ok:
            _log(f"[링크] 방법3 실패 → 방법4(execCommand) 시도")
            driver.execute_script("""
                var input = arguments[0];
                input.focus();
                input.select();
                document.execCommand('selectAll', false, null);
                document.execCommand('insertText', false, arguments[1]);
            """, input_field, url)
            time.sleep(0.5)
            val, ok = _verify()

        final_val, _ = _verify()
        _log(f"[링크] ★ 최종 입력값 (전체): {final_val}")
        _log(f"[링크] ★ 원본 URL (전체):   {url}")
        _log(f"[링크] ★ 일치 여부: {'✔ 일치' if final_val == url else '✘ 불일치!'}")
        if final_val != url:
            _log(f"[링크] ★ 차이: 입력값 {len(final_val)}자 vs 원본 {len(url)}자")

        if len(final_val) < len(url) // 2:
            _log("[링크] ⚠ URL 입력 실패 — 모든 방법 실패")
            try:
                ActionChains(driver).send_keys(Keys.ESCAPE).perform()
            except Exception:
                pass
            return False

        # ── 6) 확인 버튼 클릭 ──
        confirmed = False
        time.sleep(0.3)

        # 6-A) 커스텀 레이어/팝업 내부 버튼
        confirm_selectors = [
            'button.se-custom-layer-confirm-button',
            'button[data-log="prt.urllink.apply"]',
            '.se-custom-layer button.se-popup-button-confirm',
            'button.se-popup-button-confirm',
            '.se-popup-button-area button:last-child',
        ]
        for sel in confirm_selectors:
            btns = driver.find_elements(By.CSS_SELECTOR, sel)
            for b in btns:
                try:
                    if b.is_displayed():
                        ActionChains(driver).click(b).perform()
                        confirmed = True
                        _log(f"[링크] 확인 버튼 클릭 ({sel[:40]})")
                        break
                except Exception:
                    continue
            if confirmed:
                break

        # 6-B) 텍스트로 확인 버튼 탐색 (보이는 버튼만)
        if not confirmed:
            all_btns = driver.find_elements(By.CSS_SELECTOR, 'button')
            for b in all_btns:
                try:
                    if b.is_displayed() and b.text.strip() in (
                            '확인', '적용', '저장', '링크 적용'):
                        ActionChains(driver).click(b).perform()
                        confirmed = True
                        _log(f"[링크] 확인 버튼 클릭 (텍스트: {b.text.strip()})")
                        break
                except Exception:
                    continue

        # 6-C) Enter 키 폴백
        if not confirmed:
            _log("[링크] 확인 버튼 못 찾음 → Enter 키")
            input_field.send_keys(Keys.ENTER)

        time.sleep(1.0)

        # ── 7) 확인 후 실제 저장된 URL 검증 ──
        # 이미지의 <a href="...">를 읽어서 실제 저장된 링크 확인
        try:
            saved_links = driver.execute_script("""
                var comps = document.querySelectorAll(
                    'div.se-component.se-image, div[data-type="image"].se-component');
                if (!comps.length) return [];
                var last = comps[comps.length - 1];
                var links = last.querySelectorAll('a[href]');
                var result = [];
                links.forEach(function(a) {
                    result.push(a.href);
                });
                // data-link-* 속성도 확인
                var allEls = last.querySelectorAll('[data-link-url]');
                allEls.forEach(function(el) {
                    result.push('data-link-url: ' + el.getAttribute('data-link-url'));
                });
                // se-module-data JSON 확인
                var dataEl = last.querySelector('script, [data-module], .se-module-data');
                if (dataEl) {
                    result.push('data-module: ' + dataEl.textContent.substring(0, 300));
                }
                return result;
            """)
            if saved_links:
                for sl in saved_links:
                    _log(f"[링크검증] 이미지에 저장된 링크: {sl}")
                    if url in sl:
                        _log("[링크검증] ✔ 원본 URL과 일치!")
                    else:
                        _log(f"[링크검증] ✘ 원본과 다름! 원본: {url}")
            else:
                _log("[링크검증] ⚠ 이미지에서 링크를 찾을 수 없음")
        except Exception as ve:
            _log(f"[링크검증] 검증 실패: {ve}")

        _log("[링크] ✔ 이미지에 링크 적용 완료")

        # 이미지 선택 해제 (에디터 빈 곳 클릭)
        try:
            editor_body = driver.find_element(
                By.CSS_SELECTOR, '.se-content')
            ActionChains(driver).move_to_element_with_offset(
                editor_body, 10, editor_body.size['height'] - 10
            ).click().perform()
        except Exception:
            pass
        time.sleep(0.3)
        return True

    except Exception as e:
        _log(f"[링크] ✘ 이미지 링크 추가 실패: {e}")
        try:
            ActionChains(driver).send_keys(Keys.ESCAPE).perform()
        except Exception:
            pass
        return False


def _attach_images(driver, image_paths, log):
    """다운로드된 상품 이미지를 카페 에디터에 첨부 (posting_help.py 방식)"""
    uploaded = 0
    for path in image_paths:
        if _upload_single_image(driver, path, log):
            uploaded += 1
            time.sleep(1)  # 이미지 간 간격

    if uploaded > 0:
        log(f"[이미지] 총 {uploaded}/{len(image_paths)}개 이미지 첨부 완료")
    else:
        log("[이미지] ⚠ 이미지를 첨부하지 못했습니다 (본문 작성은 완료)")


# ─────────────────────────────────────────────────────────────
# 4. 카페 리스트 파일 읽기
# ─────────────────────────────────────────────────────────────
def load_cafe_list(file_path):
    """
    카페 리스트 파일을 읽어 [{cafe_id, menu_id}] 형태로 반환합니다.

    파일 형식 (한 줄에 하나):
        카페번호,메뉴번호
        카페번호\t메뉴번호
        카페번호 메뉴번호

    Args:
        file_path: 카페 리스트 텍스트 파일 경로

    Returns:
        list[dict]: [{"cafe_id": "...", "menu_id": "..."}, ...]
    """
    cafes = []
    if not os.path.exists(file_path):
        return cafes

    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            # 여러 구분자 지원: 콤마, 탭, 공백
            parts = re.split(r"[,\t\s]+", line, maxsplit=1)
            if len(parts) >= 2:
                cafe_id = parts[0].strip()
                menu_id = parts[1].strip()
                if cafe_id and menu_id:
                    cafes.append({"cafe_id": cafe_id, "menu_id": menu_id})

    return cafes


# ─────────────────────────────────────────────────────────────
# 5. 전체 자동 포스팅 파이프라인
# ─────────────────────────────────────────────────────────────
def safe_quit_driver(driver):
    """드라이버를 안전하게 종료합니다."""
    if driver is None:
        return
    try:
        driver.quit()
    except Exception:
        pass


def wrap_text_for_mobile(text, max_cols=45):
    """
    모바일 가독성을 위한 줄바꿈 처리.
    max_cols 자 이내로 줄을 끊되, URL/이모지/마커 등은 보존합니다.
    """
    import re as _re
    url_pat = _re.compile(r'https?://\S+')
    result_lines = []
    for line in text.split("\n"):
        stripped = line.strip()
        # 빈 줄, URL 전용 줄, 이미지 마커, 링크버튼 마커는 그대로
        if (not stripped or url_pat.fullmatch(stripped)
                or stripped.startswith("📸")
                or "🔗" in stripped
                or "[링크버튼]" in stripped):
            result_lines.append(line)
            continue
        # 이미 짧으면 그대로
        if len(stripped) <= max_cols:
            result_lines.append(line)
            continue
        # 긴 줄 → 끊기
        buf = ""
        for ch in stripped:
            buf += ch
            if len(buf) >= max_cols:
                # 마침표, 쉼표, 공백 근처에서 끊기 시도
                cut = -1
                for sep in (".", ",", " ", "!", "?"):
                    idx = buf.rfind(sep)
                    if idx > max_cols // 2:
                        cut = idx + 1
                        break
                if cut < 0:
                    cut = max_cols
                result_lines.append(buf[:cut])
                buf = buf[cut:].lstrip()
        if buf:
            result_lines.append(buf)
    return "\n".join(result_lines)


def run_auto_posting(
    login_id,
    password,
    cafes,
    keywords,
    gemini_api_key,
    search_limit=5,
    image_save_dir="images",
    log=None,
    stop_flag=None,
    driver_holder=None,
    keyword_repeat_min=3,
    keyword_repeat_max=7,
    posting_interval_min=5,
    posting_interval_max=30,
    linebreak_enabled=False,
    linebreak_max_chars=45,
    link_btn_image=None,       # (하위호환 유지, 미사용)
    coupang_access_key=None,
    coupang_secret_key=None,
    paid_members=None,
    referrer=None,
    post_count=None,
    use_product_name=False,
    category="건강식품",
    commission_image_folder=None,
    program_username=None,
):
    """
    전체 자동 포스팅 파이프라인 (유료회원/본인/추천인 교차 발행):
        유료회원 글 → 본인 글 → 유료회원 글 → 본인 글 → (추천인 있으면) 추천인 글 → 본인 글 → ... 반복

    paid_members가 제공되면 교차 발행 모드로 동작합니다.
    referrer가 있으면 paid,own,paid,own,referrer,own 패턴으로 발행합니다.
    paid_members가 None 또는 빈 리스트이면 본인 글만 발행합니다.

    Args:
        login_id: 네이버 아이디
        password: 네이버 비밀번호
        cafes: [{"cafe_id", "menu_id"}, ...] 카페 리스트
        keywords: 검색 키워드 리스트 (본인 키워드)
        gemini_api_key: Gemini API 키
        search_limit: 검색 결과 수
        image_save_dir: 이미지 저장 경로
        log: 로그 콜백 함수
        stop_flag: 중지 플래그 확인 함수 (callable, True 반환 시 중지)
        driver_holder: dict - driver 참조 외부 접근용
        posting_interval_min, posting_interval_max: 포스팅 주기 범위 (분, 랜덤)
        linebreak_enabled: 모바일 가독성 줄바꿈 사용 여부
        linebreak_max_chars: 줄바꿈 시 한 줄 최대 글자 수
        link_btn_image: (미사용, 하위호환 유지)
        coupang_access_key: 본인 쿠팡 Access Key
        coupang_secret_key: 본인 쿠팡 Secret Key
        paid_members: 유료회원 리스트 (Supabase에서 가져온 데이터)
            [{"name", "keywords": [...], "coupang_access_key", "coupang_secret_key"}, ...]
        referrer: 추천인 정보 (fetch_referrer 반환값) — None이면 추천인 글 미포함

    Returns:
        dict: {"success": 성공 수, "fail": 실패 수, "total": 전체 수}
    """
    import os
    from main import run_pipeline
    from supabase_client import fetch_banned_brands, is_keyword_banned, insert_post_log

    _log = log or print
    _stop = stop_flag or (lambda: False)

    if program_username is None:
        try:
            from auth import get_session
            s = get_session()
            program_username = (s or {}).get("username", "") or ""
        except Exception:
            program_username = ""

    server_name = os.getenv("SERVER_NAME", "PC-LOCAL")

    banned_brands = []
    try:
        banned_brands = fetch_banned_brands(log=_log)
    except Exception as e:
        _log(f"[Supabase] 활동금지 브랜드 조회 실패: {e}")

    has_paid = bool(paid_members)
    success = 0
    fail = 0
    driver = None

    # ── 포스팅 작업 목록 생성 (유료회원/본인 교차) ──
    # 각 작업: {"type", "keyword", "ak", "sk", "member_name", "category"}
    tasks = []

    if has_paid:
        # 교차 발행: paid,own,paid,own,(referrer,own)? 반복
        has_referrer = bool(referrer)
        pattern = ["paid", "own", "paid", "own", "referrer", "own"] if has_referrer else ["paid", "own", "paid", "own"]
        own_slots_per_cycle = 3 if has_referrer else 2
        kw_list = keywords if keywords else [""]
        cycles = max(1, (len(kw_list) + own_slots_per_cycle - 1) // own_slots_per_cycle)

        for _ in range(cycles):
            for slot in pattern:
                if slot == "paid":
                    member = random.choice(paid_members)
                    tasks.append({
                        "type": "paid",
                        "keyword": random.choice(member["keywords"]),
                        "ak": member["coupang_access_key"],
                        "sk": member["coupang_secret_key"],
                        "member_name": member["name"],
                        "category": member.get("category", "기타"),
                    })
                elif slot == "own":
                    kw = random.choice(kw_list)
                    tasks.append({
                        "type": "own",
                        "keyword": kw,
                        "ak": coupang_access_key,
                        "sk": coupang_secret_key,
                        "member_name": "본인",
                        "category": category,
                    })
                elif slot == "referrer" and has_referrer:
                    tasks.append({
                        "type": "referrer",
                        "keyword": random.choice(referrer["keywords"]),
                        "ak": referrer["coupang_access_key"],
                        "sk": referrer["coupang_secret_key"],
                        "member_name": referrer["name"],
                        "category": referrer.get("category", "기타"),
                    })
    else:
        # 유료회원 없음: 본인 글만 발행 (랜덤 순서)
        kw_list = list(keywords) if keywords else []
        random.shuffle(kw_list)
        for kw in kw_list:
            tasks.append({
                "type": "own",
                "keyword": kw,
                "ak": coupang_access_key,
                "sk": coupang_secret_key,
                "member_name": "본인",
                "category": category,
            })

    # post_count로 카페당 발행 개수 제한
    if post_count and post_count > 0 and len(tasks) > post_count:
        _log(f"[설정] 발행 개수 제한: {len(tasks)}건 → {post_count}건")
        tasks = tasks[:post_count]

    # 카페당 키워드 하나씩: 작업1→카페1, 작업2→카페2, 작업3→카페3, 작업4→카페1, ...
    total = len(tasks)

    def _cleanup():
        """브라우저 정리 (정상 종료 및 중지 모두에서 호출)"""
        nonlocal driver
        if driver:
            safe_quit_driver(driver)
            driver = None
            if driver_holder is not None:
                driver_holder["driver"] = None
            _log("[정리] 크롬 브라우저 종료 완료")

    _log("=" * 55)
    _log("  네이버 카페 자동 포스팅 시작")
    if has_paid:
        mode = "유료회원/본인" + ("/추천인" if referrer else "") + " 교차 발행"
        _log(f"  모드: {mode} (유료회원 {len(paid_members)}명)")
    else:
        _log(f"  모드: 본인 글 전용")
    _log(f"  작업: {len(tasks)}건 | 카페: {len(cafes)}개 (카페당 키워드1씩) | 총: {total}건")
    _log("=" * 55)

    # 1. 브라우저 준비 & 로그인
    _log("\n[Step 1] 브라우저 준비 중...")
    try:
        driver = setup_driver()
        if driver_holder is not None:
            driver_holder["driver"] = driver
        _log("[Step 1] ✔ 크롬 브라우저 준비 완료")
    except Exception as e:
        _log(f"[Step 1] ✘ 브라우저 준비 실패: {e}")
        return {"success": 0, "fail": total, "total": total}

    if _stop():
        _log("\n[중지] 사용자가 작업을 중지했습니다.")
        _cleanup()
        return {"success": 0, "fail": total, "total": total}

    _log("\n[Step 2] 네이버 로그인 중...")
    if not login_to_naver(driver, login_id, password, log=_log):
        _log("[Step 2] ✘ 로그인 실패. 작업을 중단합니다.")
        _cleanup()
        return {"success": 0, "fail": total, "total": total}

    _log("[Step 2] ✔ 로그인 성공")

    # 2. 작업별 → 카페별 포스팅 (유료회원/본인 교차)
    count = 0
    stopped = False
    last_output_file = None  # SaaS 에이전트 모드용 result_url

    for task_idx, task in enumerate(tasks):
        if _stop():
            stopped = True
            break

        task_type = task["type"]
        keyword = task["keyword"]
        task_ak = task["ak"]
        task_sk = task["sk"]
        member_name = task["member_name"]
        task_category = task.get("category", "기타")

        type_label = "유료회원" if task_type == "paid" else ("추천인" if task_type == "referrer" else "본인")

        # 쿠팡 활동금지 업체/브랜드 체크
        if is_keyword_banned(keyword, banned_brands):
            _log(f"\n⚠ 해당 키워드는 쿠팡 활동금지 업체 브랜드 키워드 입니다: {keyword}")
            _log(f"  → 다음 작업으로 이동합니다.")
            continue

        _log(f"\n{'━' * 50}")
        _log(f"  [{type_label}] 작업 [{task_idx + 1}/{len(tasks)}]: {keyword}")
        if task_type == "paid":
            _log(f"  회원: {member_name} | 카테고리: {task_category}")
        else:
            _log(f"  카테고리: {task_category}")
        _log(f"{'━' * 50}")

        # 상품 검색 → Gemini 요약 → 링크 변환
        _log(f"[Step 3] [{type_label}] 상품 검색 + Gemini 요약 + 링크 변환 중...")
        try:
            result = run_pipeline(
                keyword,
                limit=search_limit,
                gemini_api_key=gemini_api_key,
                log_callback=_log,
                image_save_dir=image_save_dir,
                keyword_repeat_min=keyword_repeat_min,
                keyword_repeat_max=keyword_repeat_max,
                coupang_access_key=task_ak,
                coupang_secret_key=task_sk,
                use_product_name=use_product_name,
                category=task_category,
            )
        except Exception as e:
            _log(f"[Step 3] ✘ 파이프라인 실패: {e}")
            fail += 1
            continue

        if not result:
            _log(f"[Step 3] ✘ '{keyword}' 결과 없음. 다음 작업으로 이동.")
            fail += 1
            continue

        last_output_file = result.get("output_file") or last_output_file
        post_content = result.get("post_content", "")
        image_paths_dict = result.get("image_paths", {})
        products = result.get("products", [])

        if not post_content:
            _log("[Step 3] ✘ 게시글 내용이 비어있습니다.")
            fail += 1
            continue

        # 상품 순서에 맞춰 이미지 경로 리스트 생성
        ordered_images = []
        for p in products:
            pname = p.get("productName", "")
            img_path = image_paths_dict.get(pname, "")
            if img_path and os.path.isfile(img_path):
                ordered_images.append(img_path)
                _log(f"  📸 {pname[:25]}... → {os.path.basename(img_path)}")

        # 제목과 본문 분리
        title, body = _split_title_body(post_content)
        body = _strip_part_markers(body)
        title = _strip_part_markers(title)

        # 쿠팡 파트너스 수수료 이미지: 본문 하단에 폴더 내 랜덤 1장 삽입
        product_image_count = len(ordered_images)
        if commission_image_folder and os.path.isdir(commission_image_folder):
            IMG_EXTS = (".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp")
            candidates = [
                os.path.join(commission_image_folder, f)
                for f in os.listdir(commission_image_folder)
                if f.lower().endswith(IMG_EXTS) and os.path.isfile(os.path.join(commission_image_folder, f))
            ]
            if candidates:
                footer_img = random.choice(candidates)
                ordered_images.append(footer_img)
                body = body.rstrip() + "\n\n📸 [상품 이미지]\n"
                _log(f"[Step 3] 📸 쿠팡 파트너스 수수료 이미지(하단): {os.path.basename(footer_img)}")

        # 모바일 가독성 줄바꿈 적용
        if linebreak_enabled and linebreak_max_chars > 0:
            body = wrap_text_for_mobile(body, max_cols=linebreak_max_chars)
            _log(f"[Step 3] 📱 모바일 줄바꿈 적용 (최대 {linebreak_max_chars}자)")

        _log(f"[Step 3] ✔ [{type_label}] 게시글 준비 완료 (제목: {title[:40]}...)")
        _log(f"[Step 3] 📸 상품별 이미지: {len(ordered_images)}개 매핑됨")

        # 작업당 카페 1개: 작업 순서대로 카페에 라운드로빈 배정
        cafe_idx = task_idx % len(cafes)
        cafe = cafes[cafe_idx]
        cafe_id = cafe["cafe_id"]
        menu_id = cafe["menu_id"]

        if _stop():
            stopped = True
            break

        count += 1
        _log(f"\n  ── [{count}/{total}] [{type_label}] 카페 {cafe_id}, 메뉴 {menu_id} ──")

        ok = write_cafe_post(
            driver, cafe_id, menu_id,
            title, body,
            image_map=ordered_images,
            keyword=keyword,
            log=_log,
        )

        if ok:
            _log(f"  ✔ [{type_label}] 포스팅 완료 — 댓글 작성 시작...")
            comment_ok = write_comment(driver, products, log=_log)
            if comment_ok:
                _log(f"  ✔ [{type_label}] 댓글(구매링크) 작성 완료")
            else:
                _log(f"  ⚠ [{type_label}] 댓글 작성 실패 (포스팅은 성공)")
            success += 1
            # post_logs 테이블에 기록
            try:
                posting_url = driver.current_url if driver else None
                if program_username:
                    pt = "self" if task_type == "own" else ("paid" if task_type == "paid" else "referrer")
                    partner_id = None
                    for p in products:
                        url = p.get("productUrl") or p.get("original_url")
                        if url and "lptag=" in url.lower():
                            try:
                                from urllib.parse import urlparse, parse_qs
                                qs = parse_qs(urlparse(url).query)
                                partner_id = (qs.get("lptag") or [None])[0]
                                if partner_id:
                                    break
                            except Exception:
                                pass
                    insert_post_log(
                        program_username=program_username,
                        keyword=keyword,
                        posting_url=posting_url,
                        server_name=server_name,
                        post_type=pt,
                        partner_id=partner_id,
                        log=_log,
                    )
            except Exception as e:
                _log(f"  ⚠ [post_logs] 기록 실패 (무시): {e}")
        else:
            fail += 1

        # 연속 포스팅 간 대기 (랜덤)
        is_last = (task_idx == len(tasks) - 1)
        if not _stop() and not is_last:
            wait_min = random.randint(
                min(posting_interval_min, posting_interval_max),
                max(posting_interval_min, posting_interval_max)
            )
            wait_sec = wait_min * 60
            _log(f"  ⏱ 포스팅 주기: {wait_min}분 대기 중... (범위: {posting_interval_min}~{posting_interval_max}분)")
            for elapsed in range(wait_sec):
                if _stop():
                    stopped = True
                    break
                if elapsed > 0 and elapsed % 60 == 0:
                    _log(f"  ⏱ {wait_sec // 60 - elapsed // 60}분 남음...")
                time.sleep(1)

        # 모든 카페에 포스팅 완료 → 상품 이미지만 삭제 (수수료 이미지는 사용자 폴더라 유지)
        if product_image_count > 0:
            for img_p in ordered_images[:product_image_count]:
                try:
                    if os.path.isfile(img_p):
                        os.remove(img_p)
                except Exception:
                    pass
            _log(f"  🗑 상품 이미지 {product_image_count}개 삭제 완료")

        if stopped:
            break

    # 3. 정리
    if stopped:
        _log(f"\n{'=' * 55}")
        _log(f"  작업이 중지되었습니다.")
        _log(f"  성공: {success} | 실패: {fail} | 처리: {count}/{total}")
        _log(f"{'=' * 55}")
    else:
        _log(f"\n{'=' * 55}")
        _log(f"  자동 포스팅 완료!")
        _log(f"  성공: {success} | 실패: {fail} | 총: {total}")
        _log(f"{'=' * 55}")

    _cleanup()
    return {"success": success, "fail": fail, "total": total, "output_file": last_output_file}


def _strip_part_markers(text):
    """본문에서 파트 A/B, 형식 표시 등 구조 표시 라인을 제거합니다."""
    if not text or not isinstance(text, str):
        return text
    # 제거할 패턴: 파트 A/B, 상품별 요약, XXX 형식, 공감형 도입 등
    patterns = [
        r'^\s*(#{1,3}\s*|\[\s*|✅\s*)?파트\s+[AB](?:\s*(?::|：).*)?\s*\]?\s*$',  # ## 파트 A, 파트 B: 상품별 요약 - 건강식품 형식 등
        r'^\s*상품별\s*요약\s*(?:[-–]\s*(?:건강식품|생활용품|가전제품|유아/출산|기타)\s*형식)?\s*$',  # 상품별 요약, 상품별 요약 - 건강식품 형식
        r'^\s*(?:건강식품|생활용품|가전제품|유아/출산|기타)\s*형식\s*$',  # 건강식품 형식 등
        r'^\s*공감형\s*도입\s*$',  # 공감형 도입
        r'^\s*불편했던\s*상황\s*제시\s*$',
        r'^\s*기존\s*제품과\s*비교\s*도입\s*$',
        r'^\s*안전성\s*강조\s*도입\s*$',
        r'^\s*제품\s*소개\s*도입\s*$',
    ]
    compiled = [re.compile(p) for p in patterns]
    lines = text.split("\n")
    result = []
    for line in lines:
        stripped = line.strip()
        if any(p.match(stripped) for p in compiled):
            continue
        result.append(line)
    return "\n".join(result)


def _split_title_body(post_content):
    """게시글 내용에서 제목과 본문을 분리합니다."""
    title = ""
    body = post_content

    # [제목] ... [본문] ... 형식으로 분리
    if "[제목]" in post_content and "[본문]" in post_content:
        parts = post_content.split("[본문]", 1)
        title_part = parts[0].replace("[제목]", "").strip()
        body = parts[1].strip() if len(parts) > 1 else ""

        # 제목에서 첫 줄만 사용
        title_lines = [l.strip() for l in title_part.split("\n") if l.strip()]
        title = title_lines[0] if title_lines else ""
    else:
        # 첫 줄을 제목으로 사용
        lines = post_content.strip().split("\n")
        title = lines[0].strip() if lines else "추천 상품 모음"
        body = "\n".join(lines[1:]).strip() if len(lines) > 1 else ""

    return title, body

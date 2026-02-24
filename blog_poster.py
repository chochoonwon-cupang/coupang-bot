# ============================================================
# 네이버 블로그 자동 포스팅 모듈 (Selenium)
# ============================================================
# posting_help.py 블로그 포스팅 로직 참고
# cafe_poster와 동일한 구조로 네이버 블로그 글쓰기
# ============================================================

import time
import random
import os
import re

# cafe_poster에서 공통 로직 재사용
from cafe_poster import (
    setup_driver,
    login_to_naver,
    _ensure_selenium,
)
from cafe_poster import (
    type_slowly, _prepare_image_with_border_and_keyword,
    wrap_text_for_mobile,
    _type_with_format, _strip_part_markers, _upload_single_image,
)
# By, Keys, ActionChains, WebDriverWait, EC는 cafe_poster 지연로딩 시 None이 될 수 있으므로 selenium에서 직접 import
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

BLOG_WRITE_URL = "https://blog.naver.com/GoBlogWrite.naver"


def _clean_blog_title(title):
    """제목에서 ## 마커 및 [정보형], [일반형] 등 형식 이름 제거 (posting_help 참고)"""
    if not title:
        return title
    clean = title.replace("## ", "").replace("##", "").strip()
    clean = re.sub(r'^\[(정보형|일반형|후기형|질문형)\]\s*', '', clean)
    return clean.strip()


def _close_popups_if_exists(driver, log=None):
    """글쓰기 화면 내 안내 팝업 등을 닫음 (posting_help 참고)"""
    _log = log or print
    try:
        script_cancel = """
        var btn = document.querySelector('.se-popup-button-cancel');
        if (btn) { btn.click(); return true; }
        return false;
        """
        if driver.execute_script(script_cancel):
            time.sleep(0.5)
        script_help = """
        var btn2 = document.querySelector('.se-help-panel-close-button');
        if (btn2) { btn2.click(); return true; }
        return false;
        """
        if driver.execute_script(script_help):
            time.sleep(0.5)
    except Exception as e:
        _log(f"[블로그] 팝업 닫기 중 오류(무시): {e}")


def _build_tags_from_keyword(keyword, max_count):
    """키워드 기반 태그 리스트 생성 (posting_help 참고)"""
    tags = []
    if not keyword:
        return tags
    tags.append(keyword.strip())
    bracket_matches = re.findall(r'\(([^)]+)\)', keyword)
    for match in bracket_matches:
        if match.strip() and match.strip() not in tags:
            tags.append(match.strip())
    for word in keyword.split():
        word_clean = word.strip('(),.?!')
        if word_clean and len(word_clean) > 1 and word_clean not in tags:
            tags.append(word_clean)
    return tags[:max_count]


def _split_title_body(text):
    """[제목]/[본문] 마커로 분리"""
    if not text:
        return "", ""
    title = ""
    body = text
    if "[제목]" in text and "[본문]" in text:
        parts = text.split("[본문]", 1)
        title_part = parts[0].replace("[제목]", "").replace("[제목]\n", "").strip()
        title = title_part.split("\n")[0].strip() if title_part else ""
        body = parts[1].strip() if len(parts) > 1 else ""
    elif "[제목]" in text:
        parts = text.split("[제목]", 1)
        rest = parts[1].strip() if len(parts) > 1 else ""
        lines = rest.split("\n", 1)
        title = lines[0].strip() if lines else ""
        body = lines[1].strip() if len(lines) > 1 else ""
    return title, body


BOLD_PATTERN = re.compile(r'^\*\*(.+?)\*\*$')
SUBTITLE_PREFIX = "✅ "
HIGHLIGHT_PATTERN = re.compile(r'\[C\](.*?)\[/C\]', re.DOTALL)


def _move_cursor_to_end(driver, log=None):
    """커서를 본문 맨 끝으로 이동 (이미지 아래에 글 쓰기 위해).
    Ctrl+End, 마지막 요소 클릭, JS Selection 순으로 시도."""
    _log = log or print
    try:
        # 1) Ctrl+End: 문서 끝으로 이동 (대부분 에디터에서 동작)
        try:
            ActionChains(driver).key_down(Keys.CONTROL).send_keys(Keys.END).key_up(Keys.CONTROL).perform()
            time.sleep(0.15)
        except Exception:
            pass
        # 2) 마지막 이미지 클릭 후 아래로: 이미지 선택 시 ENTER로 새 문단 생성
        try:
            comps = driver.find_elements(
                By.CSS_SELECTOR,
                ".se-component.se-image, .se-module-image, div[data-type='image']"
            )
            if comps:
                last_img = comps[-1]
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", last_img)
                time.sleep(0.2)
                ActionChains(driver).move_to_element(last_img).click().perform()
                time.sleep(0.2)
        except Exception:
            pass
        # 3) JS: 마지막 텍스트/이미지 섹션에 커서 이동
        try:
            driver.execute_script("""
                var sel = '.se-module-text, .se-section-text, .se-module-image, .se-component.se-image';
                var els = document.querySelectorAll(sel);
                var el = els.length > 0 ? els[els.length - 1] : null;
                if (!el) return;
                el.focus();
                var r = document.createRange();
                if (el.classList.contains('se-module-image') || el.classList.contains('se-component')) {
                    r.setStartAfter(el);
                    r.collapse(true);
                } else {
                    r.selectNodeContents(el);
                    r.collapse(false);
                }
                var s = window.getSelection();
                s.removeAllRanges();
                s.addRange(r);
            """)
            time.sleep(0.15)
        except Exception:
            pass
    except Exception as e:
        _log(f"[블로그] 커서 이동 중 오류(무시): {e}")


def write_blog_post(
    driver, title, body, image_map=None, keyword=None, log=None,
    linebreak_enabled=False, linebreak_max_chars=45,
    bg_highlight_lines=0,
    stop_flag=None,
):
    """
    네이버 블로그에 글을 작성합니다.
    posting_help.py write_text_only_blog_post 로직 참고 (mainFrame iframe, 팝업닫기, 2단계 발행)
    """
    _log = log or print
    _stop = stop_flag or (lambda: False)
    temp_paths = []
    accent_color = (random.randint(40, 120), random.randint(40, 120), random.randint(40, 120)) if keyword else None

    try:
        if _stop():
            _log("[블로그] 중지 요청으로 글쓰기 취소")
            return False
        # 1. 글쓰기 페이지 이동 (posting_help go_to_blog_write)
        _log("[블로그] 글쓰기 페이지 이동...")
        driver.get(BLOG_WRITE_URL)
        time.sleep(2)

        # 2. mainFrame iframe 전환 (posting_help: frame_to_be_available_and_switch_to_it)
        _log("[블로그] mainFrame iframe 전환 중...")
        WebDriverWait(driver, 15).until(
            EC.frame_to_be_available_and_switch_to_it((By.CSS_SELECTOR, "#mainFrame"))
        )
        time.sleep(1)

        # 3. 팝업 닫기 (posting_help close_popups_if_exists)
        _log("[블로그] 팝업 닫기 시도 중...")
        _close_popups_if_exists(driver, _log)

        # 4. 제목 입력 (posting_help: .se-section-documentTitle)
        clean_title_text = _clean_blog_title(_strip_part_markers(
            title.replace("[제목]", "").replace("[제목]\n", "").strip()
        ))
        if len(clean_title_text) > 100:
            clean_title_text = clean_title_text[:97] + "..."
        _log(f"[블로그] 제목 입력 중... ({clean_title_text[:50]}...)")
        title_section = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".se-section-documentTitle"))
        )
        title_section.click()
        time.sleep(0.5)
        type_slowly(driver, clean_title_text, delay=0.03)
        time.sleep(0.5)

        # 5. 본문 입력 (posting_help: .se-section-text)
        clean_body = body.replace("[본문]", "").replace("[본문]\n", "").strip()
        clean_body = _strip_part_markers(clean_body)
        if linebreak_enabled and linebreak_max_chars > 0:
            clean_body = wrap_text_for_mobile(clean_body, max_cols=linebreak_max_chars)
            _log(f"[블로그] 📱 모바일 줄바꿈 적용 (최대 {linebreak_max_chars}자)")

        _log("[블로그] 본문 입력 중...")
        body_section = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".se-section-text"))
        )
        body_section.click()
        time.sleep(0.5)

        ordered_images = list(image_map or [])
        image_idx = 0
        IMAGE_MARKER = "📸 [상품 이미지]"
        lines = clean_body.split("\n")
        BG_COLORS = ["#fff8b2", "#fff593", "#fdd5f5", "#ffb7de", "#ffe3c8", "#e3fdc8", "#c2f4db"]

        # 배경색 적용 대상 줄 (posting_help: 빈줄/##/[사진]/이미지마커 제외, 랜덤 선택)
        bg_target_indices = set()
        if bg_highlight_lines > 0 and lines:
            candidate_indices = [
                i for i, ln in enumerate(lines)
                if ln.strip()
                and not ln.strip().startswith("##")
                and ln.strip() != "[사진]"
                and IMAGE_MARKER not in ln.strip()
            ]
            if candidate_indices:
                k = min(bg_highlight_lines, len(candidate_indices))
                bg_target_indices = set(random.sample(candidate_indices, k))

        def _apply_bg_highlight(line_idx):
            """현재 줄에 배경색 적용 (posting_help: 툴바 버튼 클릭 방식)"""
            if line_idx not in bg_target_indices:
                return
            try:
                ActionChains(driver).key_down(Keys.SHIFT).send_keys(Keys.HOME).key_up(Keys.SHIFT).perform()
                time.sleep(0.2)
                bg_btn = WebDriverWait(driver, 3).until(
                    EC.element_to_be_clickable((
                        By.CSS_SELECTOR,
                        "button.se-property-toolbar-color-picker-button.se-background-color-toolbar-button"
                    ))
                )
                bg_btn.click()
                time.sleep(0.3)
                color_hex = random.choice(BG_COLORS)
                palette_sel = f"button.se-color-palette[data-color='{color_hex}']"
                palette_btn = None
                try:
                    palette_btn = WebDriverWait(driver, 2).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, palette_sel))
                    )
                except Exception:
                    for c in BG_COLORS:
                        try:
                            palette_btn = driver.find_element(By.CSS_SELECTOR, f"button.se-color-palette[data-color='{c}']")
                            break
                        except Exception:
                            continue
                if palette_btn:
                    palette_btn.click()
                    time.sleep(0.3)
                    _log(f"[블로그] 배경색 {color_hex} 적용 (줄 {line_idx+1})")
                    ActionChains(driver).send_keys(Keys.END).perform()
                    time.sleep(0.1)
                    try:
                        bg_btn.click()
                        time.sleep(0.2)
                        no_color = WebDriverWait(driver, 3).until(
                            EC.element_to_be_clickable((
                                By.CSS_SELECTOR,
                                "button.se-color-palette.se-color-palette-no-color"
                            ))
                        )
                        no_color.click()
                        time.sleep(0.2)
                    except Exception:
                        pass
            except Exception as e_bg:
                _log(f"[블로그] 배경색 적용 중 오류(무시): {e_bg}")

        for i, line in enumerate(lines):
            if _stop():
                _log("[블로그] 중지 요청으로 본문 입력 중단")
                return False
            stripped = line.strip()
            if IMAGE_MARKER in stripped and image_idx < len(ordered_images):
                img_path = ordered_images[image_idx]
                if keyword and image_idx == 0:
                    prepared = _prepare_image_with_border_and_keyword(
                        img_path, keyword, accent_color=accent_color, log=_log
                    )
                    if prepared != img_path:
                        temp_paths.append(prepared)
                        img_path = prepared
                _log(f"[블로그] 이미지 삽입: {os.path.basename(str(img_path))}")
                _upload_single_image(driver, img_path, _log, click_last_section=True)
                image_idx += 1
                time.sleep(0.8)  # 이미지 섹션 DOM 업데이트 대기
                _move_cursor_to_end(driver, _log)
                ActionChains(driver).send_keys(Keys.ENTER).perform()
                time.sleep(0.5)
                # ENTER로 생성된 새 문단에 포커스: 마지막 텍스트 섹션 클릭
                try:
                    text_els = driver.find_elements(By.CSS_SELECTOR, ".se-module-text, .se-section-text")
                    if text_els:
                        last_txt = text_els[-1]
                        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", last_txt)
                        time.sleep(0.2)
                        last_txt.click()
                        time.sleep(0.2)
                except Exception:
                    pass
            elif BOLD_PATTERN.match(stripped):
                bold_text = BOLD_PATTERN.match(stripped).group(1)
                ActionChains(driver).key_down(Keys.CONTROL).send_keys('b').key_up(Keys.CONTROL).perform()
                time.sleep(0.1)
                type_slowly(driver, bold_text, delay=0.02)
                ActionChains(driver).key_down(Keys.CONTROL).send_keys('b').key_up(Keys.CONTROL).perform()
                time.sleep(0.1)
                _apply_bg_highlight(i)
                if i < len(lines) - 1:
                    ActionChains(driver).send_keys(Keys.ENTER).perform()
                    time.sleep(0.05)
            elif stripped.startswith(SUBTITLE_PREFIX):
                _type_with_format(driver, stripped, is_subtitle=True, delay=0.02)
                _apply_bg_highlight(i)
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
                _apply_bg_highlight(i)
                if i < len(lines) - 1:
                    ActionChains(driver).send_keys(Keys.ENTER).perform()
                    time.sleep(0.05)
            else:
                if i < len(lines) - 1:
                    ActionChains(driver).send_keys(Keys.ENTER).perform()
                    time.sleep(0.05)

        _log("[블로그] 본문 입력 완료")
        time.sleep(0.5)

        # 6. 1차 발행 버튼 클릭 (posting_help: CSS 셀렉터 + 텍스트 탐색, default_content → mainFrame)
        _log("[블로그] 1차 발행 버튼 클릭 중...")
        publish_click_script = """
        var selectors = [
          '.publish_btn__m9KHH', '.publish_btn__Y5zDv',
          'button[aria-label="발행"]', 'button[aria-label="등록"]',
          'button[type="button"].btn_post', 'button[type="button"].btn_publish',
          'button.confirm_btn__WEaBq', 'button[data-testid="seOnePublishBtn"]'
        ];
        for (var s = 0; s < selectors.length; s++) {
          var btn = document.querySelector(selectors[s]);
          if (btn && !btn.disabled) {
            btn.scrollIntoView({behavior: 'smooth', block: 'center'});
            btn.click();
            return true;
          }
        }
        var btns = document.querySelectorAll('button');
        for (var i = 0; i < btns.length; i++) {
          var t = (btns[i].innerText || btns[i].textContent || '').trim();
          if (t === '발행' || t === '발행하기' || t === '등록' || t.indexOf('발행') >= 0) {
            btns[i].scrollIntoView({behavior: 'smooth', block: 'center'});
            btns[i].click();
            return true;
          }
        }
        return false;
        """
        clicked_first = False
        try:
            driver.switch_to.default_content()
            for _ in range(5):
                clicked_first = driver.execute_script(publish_click_script)
                if clicked_first:
                    _log("[블로그] 1차 발행 버튼 클릭 완료 (기본 문서)")
                    break
                time.sleep(1)
        except Exception as e:
            _log(f"[블로그] 1차 발행 기본 문서 클릭 중 예외(무시): {e}")
        if not clicked_first:
            try:
                WebDriverWait(driver, 10).until(
                    EC.frame_to_be_available_and_switch_to_it((By.CSS_SELECTOR, "#mainFrame"))
                )
                for _ in range(5):
                    clicked_first = driver.execute_script(publish_click_script)
                    if clicked_first:
                        _log("[블로그] 1차 발행 버튼 클릭 완료 (mainFrame)")
                        break
                    time.sleep(1)
            except Exception as e:
                _log(f"[블로그] 1차 발행 mainFrame 클릭 중 예외(무시): {e}")
            finally:
                try:
                    driver.switch_to.default_content()
                except Exception:
                    pass
        if not clicked_first:
            _log("[블로그] 1차 발행 JS 실패, Selenium 직접 클릭 시도...")
            try:
                driver.switch_to.default_content()
                for sel in [".publish_btn__m9KHH", ".publish_btn__Y5zDv", "button[aria-label='발행']", "button[aria-label='등록']"]:
                    try:
                        btn = driver.find_element(By.CSS_SELECTOR, sel)
                        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
                        time.sleep(0.5)
                        btn.click()
                        clicked_first = True
                        _log("[블로그] 1차 발행 Selenium 클릭 완료")
                        break
                    except Exception:
                        continue
                if not clicked_first:
                    btns = driver.find_elements(By.TAG_NAME, "button")
                    for b in btns:
                        if (b.text or "").strip() in ("발행", "발행하기", "등록"):
                            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", b)
                            time.sleep(0.5)
                            b.click()
                            clicked_first = True
                            break
                if not clicked_first:
                    try:
                        WebDriverWait(driver, 5).until(
                            EC.frame_to_be_available_and_switch_to_it((By.CSS_SELECTOR, "#mainFrame"))
                        )
                        btns = driver.find_elements(By.TAG_NAME, "button")
                        for b in btns:
                            if (b.text or "").strip() in ("발행", "발행하기", "등록"):
                                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", b)
                                time.sleep(0.5)
                                b.click()
                                clicked_first = True
                                break
                    except Exception:
                        pass
                    finally:
                        try:
                            driver.switch_to.default_content()
                        except Exception:
                            pass
            except Exception as e2:
                _log(f"[블로그] 1차 발행 Selenium 클릭 실패: {e2}")

        # 7. 2차 발행: 태그 입력 및 확인 버튼 (posting_help 참고)
        time.sleep(2)
        try:
            WebDriverWait(driver, 8).until(
                EC.frame_to_be_available_and_switch_to_it((By.CSS_SELECTOR, "#mainFrame"))
            )
        except Exception:
            _log("[블로그] 태그/확인 창이 나타나지 않아 태그 입력을 생략합니다.")
            return clicked_first

        tag_input = None
        for sel in ["#tag-input.tag_input__rvUB5", "#tag-input", "input.tag_input", ".tag_input"]:
            try:
                tag_input = WebDriverWait(driver, 3).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, sel))
                )
                break
            except Exception:
                continue
        if tag_input and keyword:
            tags = _build_tags_from_keyword(keyword, 5)
            for t in tags:
                try:
                    tag_input.send_keys(t)
                    time.sleep(0.2)
                    tag_input.send_keys(Keys.ENTER)
                    time.sleep(0.2)
                except Exception:
                    continue

        _log("[블로그] 2차 발행(확인) 버튼 클릭 중...")
        confirm_script = """
        var selectors = [
          'button.confirm_btn__WEaBq[data-testid="seOnePublishBtn"]',
          'button.confirm_btn__WEaBq', 'button[data-testid="seOnePublishBtn"]',
          '.publish_btn__m9KHH', '.publish_btn__Y5zDv',
          'button[aria-label="발행"]', 'button[aria-label="등록"]'
        ];
        for (var s = 0; s < selectors.length; s++) {
          var btn = document.querySelector(selectors[s]);
          if (btn && !btn.disabled) {
            btn.scrollIntoView({behavior: 'smooth', block: 'center'});
            btn.click();
            return true;
          }
        }
        var btns = document.querySelectorAll('button');
        for (var i = 0; i < btns.length; i++) {
          var t = (btns[i].innerText || btns[i].textContent || '').trim();
          if (t === '발행' || t === '발행하기' || t === '등록') {
            btns[i].scrollIntoView({behavior: 'smooth', block: 'center'});
            btns[i].click();
            return true;
          }
        }
        return false;
        """
        clicked_confirm = False
        for _ in range(5):
            clicked_confirm = driver.execute_script(confirm_script)
            if clicked_confirm:
                _log("[블로그] ✔ 2차 발행(확인) 완료")
                break
            time.sleep(1)

        time.sleep(3)
        return True
    except Exception as e:
        import traceback
        _log(f"[블로그] ✘ 글 작성 중 오류: {e}")
        _log(traceback.format_exc())
        return False
    finally:
        for p in temp_paths:
            try:
                if os.path.isfile(p):
                    os.remove(p)
            except Exception:
                pass


def write_blog_comment(driver, products, log=None):
    """
    블로그 포스팅 완료 후 게시글 페이지에서 댓글 쓰기 클릭 → 댓글창 클릭 → 상품 링크 등록.
    카페 write_comment와 동일한 형식으로 상품 링크를 댓글로 등록합니다.
    """
    _log = log or print
    try:
        _log("[블로그 댓글] 댓글 작성 준비 중...")
        time.sleep(4)  # 발행 후 게시글 보기 페이지로 리다이렉트 대기

        # 댓글 본문 구성 (카페와 동일 형식)
        comment_lines = []
        for i, p in enumerate(products):
            name = p.get("productName", "상품")
            link = p.get("short_url", p.get("productUrl", ""))
            if not link:
                continue
            if i > 0:
                comment_lines.append("")
            short_name = name if len(name) <= 40 else name[:37] + "..."
            comment_lines.append(f"▶ {short_name}")
            comment_lines.append(link)

        if not comment_lines:
            _log("[블로그 댓글] ✘ 링크가 있는 상품이 없습니다.")
            return False

        comment_text = "\n".join(comment_lines)
        product_count = sum(1 for l in comment_lines if l.startswith("▶"))
        _log(f"[블로그 댓글] 댓글 내용 구성 완료 (상품 {product_count}개)")

        try:
            driver.switch_to.default_content()
        except Exception:
            pass

        # mainFrame 전환 (블로그 게시글 보기 페이지)
        try:
            WebDriverWait(driver, 10).until(
                EC.frame_to_be_available_and_switch_to_it((By.CSS_SELECTOR, "#mainFrame"))
            )
        except Exception:
            pass

        # 1) 댓글 쓰기 버튼 클릭 (댓글 열기)
        _log("[블로그 댓글] 댓글 쓰기 버튼 클릭 중...")
        comment_btn = None
        for sel in [
            "a.btn_comment._cmtList",
            "a.btn_comment",
            ".btn_comment",
            "a[class*='cmtList']",
            "a[class*='btn_comment']",
        ]:
            try:
                comment_btn = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, sel))
                )
                if comment_btn and comment_btn.is_displayed():
                    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", comment_btn)
                    time.sleep(0.5)
                    comment_btn.click()
                    _log("[블로그 댓글] 댓글 버튼 클릭 완료")
                    break
            except Exception:
                continue
        if not comment_btn:
            _log("[블로그 댓글] ✘ 댓글 버튼을 찾을 수 없습니다.")
            return False

        time.sleep(2.5)  # 댓글 영역 로드 대기

        # 2) 댓글 입력창 찾기 및 클릭 (댓글창 클릭)
        comment_box = None
        for sel in [
            "textarea.u_cbox_text",
            "textarea.u_cbox_content",
            ".u_cbox_text",
            ".u_cbox_inbox textarea",
            "textarea[placeholder*='댓글']",
            "textarea[placeholder*='블로그']",
            ".u_cbox_text_wrap textarea",
            ".u_cbox_guide",  # placeholder 영역 클릭 시 입력창 포커스
            "div.u_cbox_content",
            "[contenteditable='true'][data-placeholder]",
        ]:
            try:
                comment_box = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, sel))
                )
                if comment_box and comment_box.is_displayed():
                    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", comment_box)
                    time.sleep(0.5)
                    comment_box.click()
                    time.sleep(0.5)
                    _log("[블로그 댓글] 댓글창 클릭 완료")
                    break
            except Exception:
                continue

        if not comment_box:
            _log("[블로그 댓글] ✘ 댓글 입력창을 찾을 수 없습니다.")
            return False

        # 3) 댓글 입력 (상품 링크)
        try:
            _log("[블로그 댓글] 상품 링크 입력 중...")
            type_slowly(driver, comment_text, delay=0.03)
        except Exception as e:
            _log(f"[블로그 댓글] type_slowly 실패, send_keys 시도: {e}")
            try:
                comment_box.send_keys(comment_text)
            except Exception as e2:
                _log(f"[블로그 댓글] ✘ 댓글 입력 실패: {e2}")
                return False

        time.sleep(0.5)

        # 4) 등록 버튼 클릭 (u_cbox_btn_upload: 스티커/사진 옆 등록 버튼)
        try:
            for sel in [
                "button.u_cbox_btn_upload",
                "button[data-ui-selector='writeButton']",
                "button[data-action='write#request']",
                "button[data-area-code='RPC.write']",
                ".u_cbox_btn_upload",
                "button.u_cbox_btn_register",
                "a.u_cbox_btn_register",
                ".u_cbox_btn_register",
                "button[type='submit']",
                "a.button.btn_register",
                "button.button.btn_register",
            ]:
                try:
                    reg_btn = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, sel))
                    )
                    if reg_btn and reg_btn.is_displayed():
                        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", reg_btn)
                        time.sleep(0.3)
                        try:
                            reg_btn.click()
                        except Exception:
                            driver.execute_script("arguments[0].click();", reg_btn)
                        time.sleep(2)
                        _log("[블로그 댓글] ✔ 상품 링크 댓글 등록 완료!")
                        return True
                except Exception:
                    continue
            # 텍스트로 '등록' 포함된 버튼 찾기
            try:
                btns = driver.find_elements(By.CSS_SELECTOR, "button.u_cbox_btn_upload, button[class*='u_cbox']")
                for b in btns:
                    txt = (b.text or "").strip()
                    if "등록" in txt and b.is_displayed():
                        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", b)
                        time.sleep(0.3)
                        try:
                            b.click()
                        except Exception:
                            driver.execute_script("arguments[0].click();", b)
                        time.sleep(2)
                        _log("[블로그 댓글] ✔ 상품 링크 댓글 등록 완료!")
                        return True
            except Exception:
                pass
            # 댓글 영역이 iframe 안에 있으면 iframe 내에서 등록 버튼 탐색
            try:
                driver.switch_to.default_content()
                WebDriverWait(driver, 3).until(
                    EC.frame_to_be_available_and_switch_to_it((By.CSS_SELECTOR, "#mainFrame"))
                )
                iframes = driver.find_elements(By.CSS_SELECTOR, "iframe")
                for ifr in iframes:
                    try:
                        driver.switch_to.frame(ifr)
                        reg_btn = driver.find_element(By.CSS_SELECTOR, "button.u_cbox_btn_upload")
                        if reg_btn and reg_btn.is_displayed():
                            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", reg_btn)
                            time.sleep(0.3)
                            driver.execute_script("arguments[0].click();", reg_btn)
                            time.sleep(2)
                            _log("[블로그 댓글] ✔ 상품 링크 댓글 등록 완료! (iframe)")
                            return True
                    except Exception:
                        try:
                            driver.switch_to.parent_frame()
                        except Exception:
                            driver.switch_to.default_content()
                            WebDriverWait(driver, 3).until(
                                EC.frame_to_be_available_and_switch_to_it((By.CSS_SELECTOR, "#mainFrame"))
                            )
                            break
            except Exception:
                pass
            _log("[블로그 댓글] ✘ 등록 버튼을 찾을 수 없습니다.")
        except Exception as e:
            _log(f"[블로그 댓글] ✘ 등록 버튼 클릭 실패: {e}")

        return False
    except Exception as e:
        _log(f"[블로그 댓글] ✘ 댓글 작성 중 오류: {e}")
        return False
    finally:
        try:
            driver.switch_to.default_content()
        except Exception:
            pass


def run_auto_blogging(
    login_id,
    password,
    keywords,
    gemini_api_key,
    log=None,
    posting_interval_min=5,
    posting_interval_max=30,
    image_save_dir=None,
    keyword_repeat_min=3,
    keyword_repeat_max=7,
    coupang_access_key=None,
    coupang_secret_key=None,
    stop_flag=None,
    post_count=None,
    use_product_name=False,
    linebreak_enabled=False,
    linebreak_max_chars=45,
    commission_image_folder=None,
    bg_highlight_lines=0,
    paid_members=None,
    referrer=None,
    category="건강식품",
    program_username=None,
):
    """
    블로그 자동 포스팅 실행.
    유료회원/추천인 있으면 교차 발행 (카페와 동일), 없으면 본인 글만.
    """
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

    from main import run_pipeline

    banned_brands = []
    try:
        from supabase_client import fetch_banned_brands, is_keyword_banned
        banned_brands = fetch_banned_brands(log=_log)
    except Exception as e:
        _log(f"[Supabase] 활동금지 브랜드 조회 실패: {e}")
        is_keyword_banned = lambda k, b: False

    has_paid = bool(paid_members)
    success = 0
    fail = 0
    driver = None

    # ── 포스팅 작업 목록 생성 (유료회원/본인/추천인 교차) ──
    tasks = []
    if has_paid:
        has_referrer = bool(referrer)
        pattern = ["paid", "own", "paid", "own", "referrer", "own"] if has_referrer else ["paid", "own", "paid", "own"]
        own_slots_per_cycle = 3 if has_referrer else 2
        kw_list = keywords if keywords else [""]
        cycles = max(1, (len(kw_list) + own_slots_per_cycle - 1) // own_slots_per_cycle)

        for _ in range(cycles):
            for slot in pattern:
                if slot == "paid":
                    member = random.choice(paid_members)
                    mkws = member.get("keywords") or kw_list or ["건강식품"]
                    tasks.append({
                        "type": "paid",
                        "keyword": random.choice(mkws),
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
                    rkws = referrer.get("keywords") or kw_list or ["건강식품"]
                    tasks.append({
                        "type": "referrer",
                        "keyword": random.choice(rkws),
                        "ak": referrer["coupang_access_key"],
                        "sk": referrer["coupang_secret_key"],
                        "member_name": referrer["name"],
                        "category": referrer.get("category", "기타"),
                    })
    else:
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

    if post_count and post_count > 0 and len(tasks) > post_count:
        _log(f"[설정] 발행 개수 제한: {len(tasks)}건 → {post_count}건")
        tasks = tasks[:post_count]

    total = len(tasks)
    if not tasks:
        _log("[블로그] 작업 목록이 비어있습니다.")
        return {"success": 0, "fail": 0, "total": 0}

    try:
        _log("=" * 55)
        _log("  네이버 블로그 자동 포스팅 시작")
        if has_paid:
            mode = "유료회원/본인" + ("/추천인" if referrer else "") + " 교차 발행"
            _log(f"  모드: {mode} (유료회원 {len(paid_members)}명)")
        else:
            _log(f"  모드: 본인 글 전용")
        _log(f"  작업: {total}건 | 간격: {posting_interval_min}~{posting_interval_max}분 (랜덤)")
        _log("=" * 55)

        driver = setup_driver()
        _log("[Step 1] 로그인 중...")
        if not login_to_naver(driver, login_id, password):
            _log("[Step 1] ✘ 로그인 실패")
            return {"success": 0, "fail": total, "total": total}
        _log("[Step 1] ✔ 로그인 완료")

        for idx, task in enumerate(tasks):
            if _stop():
                _log("[중지] 사용자가 작업을 중지했습니다.")
                break

            keyword = task["keyword"]
            if is_keyword_banned(keyword, banned_brands):
                _log(f"\n⚠ 해당 키워드는 쿠팡 활동금지 업체 브랜드 키워드 입니다: {keyword}")
                _log(f"  → 다음 작업으로 이동합니다.")
                continue

            _log(f"\n{'━' * 50}")
            _log(f"  [{idx+1}/{total}] {keyword} ({task['member_name']})")
            _log(f"{'━' * 50}")

            try:
                result = run_pipeline(
                    keyword,
                    limit=1,
                    gemini_api_key=gemini_api_key,
                    log_callback=_log,
                    image_save_dir=image_save_dir,
                    keyword_repeat_min=keyword_repeat_min,
                    keyword_repeat_max=keyword_repeat_max,
                    coupang_access_key=task["ak"],
                    coupang_secret_key=task["sk"],
                    category=task["category"],
                    use_product_name=use_product_name,
                )
                if not result:
                    fail += 1
                    continue

                if _stop():
                    _log("[중지] 사용자가 작업을 중지했습니다.")
                    break

                post_content = result.get("post_content", "")
                products = result.get("products", [])
                image_paths_dict = result.get("image_paths", {})

                title, body = _split_title_body(post_content)
                if use_product_name and products:
                    pname = products[0].get("productName", "")
                    if pname:
                        title = f"{keyword} {pname}" if title else f"{keyword} {pname}"

                ordered_images = []
                for p in products:
                    pname = p.get("productName", "")
                    img_path = image_paths_dict.get(pname, "")
                    if img_path and os.path.isfile(img_path):
                        ordered_images.append(img_path)
                product_image_count = len(ordered_images)

                if commission_image_folder and os.path.isdir(commission_image_folder):
                    IMG_EXTS = (".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp")
                    candidates = [
                        os.path.join(commission_image_folder, f)
                        for f in os.listdir(commission_image_folder)
                        if f.lower().endswith(IMG_EXTS)
                        and os.path.isfile(os.path.join(commission_image_folder, f))
                    ]
                    if candidates:
                        footer_img = random.choice(candidates)
                        ordered_images.append(footer_img)
                        body = body.rstrip() + "\n\n📸 [상품 이미지]\n"
                        _log(f"[블로그] 수수료 이미지 추가(하단): {os.path.basename(footer_img)}")

                ok = write_blog_post(
                    driver, title, body,
                    image_map=ordered_images,
                    keyword=keyword,
                    log=_log,
                    linebreak_enabled=linebreak_enabled,
                    linebreak_max_chars=linebreak_max_chars,
                    bg_highlight_lines=bg_highlight_lines,
                    stop_flag=_stop,
                )
                if ok:
                    success += 1
                    _log(f"  ✔ [{idx+1}/{total}] 블로그 포스팅 완료")
                    if program_username:
                        try:
                            from supabase_client import insert_post_log
                            from urllib.parse import urlparse, parse_qs
                            posting_url = driver.current_url if driver else None
                            task_type = task.get("type", "own")
                            pt = "self" if task_type == "own" else ("paid" if task_type == "paid" else "referrer")
                            partner_id = None
                            for p in products:
                                url = p.get("productUrl") or p.get("original_url")
                                if url and "lptag=" in url.lower():
                                    try:
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
                    if products:
                        _log("  → 댓글(상품 링크) 작성 시작...")
                        comment_ok = write_blog_comment(driver, products, log=_log)
                        if comment_ok:
                            _log(f"  ✔ [{idx+1}/{total}] 댓글(구매링크) 작성 완료")
                        else:
                            _log(f"  ⚠ [{idx+1}/{total}] 댓글 작성 실패 (포스팅은 성공)")
                else:
                    fail += 1
                    if _stop():
                        _log("[중지] 사용자가 작업을 중지했습니다.")
                        break

                # 상품 이미지만 삭제 (수수료 이미지는 사용자 폴더라 유지)
                for img_p in ordered_images[:product_image_count]:
                    try:
                        if os.path.isfile(img_p):
                            os.remove(img_p)
                    except Exception:
                        pass

            except Exception as e:
                _log(f"  ✘ 오류: {e}")
                fail += 1

            # 다음 키워드 전 대기 (랜덤)
            if idx < total and not _stop():
                wait_min = random.randint(
                    min(posting_interval_min, posting_interval_max),
                    max(posting_interval_min, posting_interval_max)
                )
                wait_sec = wait_min * 60
                _log(f"  ⏱ {wait_min}분 대기 중... (범위: {posting_interval_min}~{posting_interval_max}분)")
                for _ in range(wait_sec):
                    if _stop():
                        break
                    time.sleep(1)

        _log(f"\n{'=' * 55}")
        _log(f"  블로그 포스팅 완료: 성공 {success} / 실패 {fail} / 총 {total}")
        _log(f"{'=' * 55}")

        return {"success": success, "fail": fail, "total": total}
    except Exception as e:
        _log(f"[오류] {e}")
        return {"success": success, "fail": fail + (total - success - fail), "total": total}
    finally:
        if driver:
            try:
                if _stop():
                    _log("[정리] 중지됨 - 브라우저를 즉시 종료합니다.")
                else:
                    _log("[정리] 5초 후 브라우저를 종료합니다...")
                    time.sleep(5)
                driver.quit()
                _log("[정리] 브라우저 종료 완료")
            except Exception:
                pass

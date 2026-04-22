#!/usr/bin/env python3
"""인터넷등기소 열람+저장+파일명변경 자동화 - 부동산등기부등본
결제 완료된 부동산등기부등본을 순서대로 열람 → 저장 → 파일명 변경합니다.
열람 후 항목이 사라지므로 항상 첫 번째 열람 버튼만 클릭합니다.
Usage: python3 iros_download_realty.py [config.json] [건수]

주의:
- TouchEn nxKey 보안 프로그램 사전 설치 필수.
- 로그인은 수동. 로그인 후 Enter 입력.
- 파일명은 기본적으로 {index}_{고유번호또는timestamp}.pdf 형식입니다.
  (법인 다운로드와 달리 상호명 매칭이 없으므로 식별자는 순번/파일 고유번호 기준)
"""
import json, sys, os, re, time, shutil
from datetime import datetime
from playwright.sync_api import sync_playwright


# ─── 셀렉터 ────────────────────────────────────────────────────

# 부동산 신청결과 확인 (열람·발급) 메뉴 ID
BTN_MENU_REALTY_APPLY_RESULT = (
    'mf_wfm_potal_main_wf_header_gen_depth1_0_gen_depth2_0'
    '_gen_depth3_6_gen_depth4_0_btn_top_menu4'
)


# ─── 유틸 ─────────────────────────────────────────────────────

def load_config(path="config.json"):
    with open(path) as f:
        return json.load(f)


def load_log(path):
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return {"completed": [], "failed": [], "skipped": []}


def save_log(log, path):
    os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
    with open(path, "w") as f:
        json.dump(log, f, ensure_ascii=False, indent=2)


def dismiss(page):
    try:
        page.evaluate("""() => {
            document.querySelectorAll('#_modal,.w2modal_popup').forEach(m => {
                m.style.display='none'; m.style.pointerEvents='none';
            });
        }""")
    except Exception:
        pass


def detect_security_install(page):
    try:
        txt = page.evaluate("document.body ? document.body.innerText : ''")
    except Exception:
        return False
    if not txt:
        return False
    return any(kw in txt for kw in ["보안 프로그램 설치", "보안프로그램 설치", "TouchEn", "nxKey"])


def snapshot_files(dl_dir):
    files = set()
    try:
        for f in os.listdir(dl_dir):
            fp = os.path.join(dl_dir, f)
            if os.path.isfile(fp):
                files.add(fp)
    except Exception:
        pass
    return files


def wait_for_new_file(before_files, dl_dir, timeout=30):
    for _ in range(timeout):
        time.sleep(1)
        current = snapshot_files(dl_dir)
        new_files = current - before_files
        for f in new_files:
            if not os.path.basename(f).endswith('.crdownload'):
                return f
    return None


def click_save(page):
    for sel in [
        'input[id*="wframe_btn_download"]',
        'input[value="저장"]',
    ]:
        try:
            page.click(sel, timeout=5000, force=True)
            return True
        except Exception:
            continue
    return False


def close_viewer(page):
    for sel in [
        'input[id*="wframe_btn_close"]',
        'input[value="닫기"]',
    ]:
        try:
            page.click(sel, timeout=3000, force=True)
            page.wait_for_timeout(1500)
            return
        except Exception:
            continue
    try:
        page.keyboard.press('Escape')
        page.wait_for_timeout(1500)
    except Exception:
        pass
    dismiss(page)


def process_one(page, log, dl_dir, save_dir, index):
    """한 건 처리: 항상 첫 번째 열람 버튼 클릭."""
    dismiss(page)

    # 1. 첫 번째 열람 버튼 클릭 + 라벨/주소 추출 (tsv에서 중간 칸)
    result = page.evaluate("""() => {
        const btns = document.querySelectorAll('button');
        for (const b of btns) {
            if (b.offsetParent !== null && b.textContent.trim() === '열람') {
                const gp = b.parentElement ? b.parentElement.parentElement : null;
                let summary = '';
                if (gp) {
                    const parts = gp.innerText.split('\\t').map(s => s.trim()).filter(Boolean);
                    summary = parts.slice(0, 6).join(' | ');
                }
                b.click();
                return {clicked: true, summary: summary};
            }
        }
        return {clicked: false, summary: ''};
    }""")

    if not result.get("clicked"):
        return ("no_more", "")

    summary = result.get("summary", "")
    print(f"{summary[:40]}", end=" ", flush=True)

    # 2. 확인 팝업
    page.wait_for_timeout(3000)
    for sel in [
        'input[id*="btn_confirm2"][value="확인"]',
        'a[id*="btn_confirm2"]',
        'input[value="확인"]',
        'button:has-text("확인")',
    ]:
        try:
            page.click(sel, timeout=2000)
            print("(확인)", end=" ", flush=True)
            break
        except Exception:
            continue

    # 3. 문서 로딩 대기
    page.wait_for_timeout(8000)

    # 4. 저장
    before_files = snapshot_files(dl_dir)
    if not click_save(page):
        print("(저장실패)", end=" ", flush=True)
        close_viewer(page)
        return ("save_fail", summary)
    print("(저장OK)", end=" ", flush=True)

    # 5. 변환 확인 팝업
    page.wait_for_timeout(2000)
    for sel in ['input[value="확인"]', 'button:has-text("확인")']:
        try:
            page.click(sel, timeout=3000)
            break
        except Exception:
            continue

    # 6. 다운로드 대기
    dl_file = wait_for_new_file(before_files, dl_dir)
    if not dl_file:
        print("다운로드안됨 X")
        close_viewer(page)
        return ("dl_fail", summary)

    # 7. 파일 처리: 확장자 보정
    if not dl_file.endswith('.pdf'):
        pdf_file = dl_file + '.pdf'
        os.rename(dl_file, pdf_file)
        dl_file = pdf_file

    # PDF 헤더 검증
    try:
        with open(dl_file, 'rb') as fh:
            header = fh.read(4)
        if header != b'%PDF':
            print("(PDF아님)", end=" ", flush=True)
    except Exception:
        pass

    # 파일명: {index}_{원본파일명_stem}.pdf
    stem = os.path.splitext(os.path.basename(dl_file))[0]
    safe_stem = re.sub(r'[\\/:*?"<>|]', '_', stem)[:40]
    new_name = f"realty_{index:04d}_{safe_stem}.pdf"
    new_path = os.path.join(save_dir, new_name)
    if os.path.exists(new_path):
        new_path = os.path.join(save_dir, f"realty_{index:04d}_{safe_stem}_{int(time.time())}.pdf")
    shutil.move(dl_file, new_path)
    print(f"-> {os.path.basename(new_path)} OK")

    close_viewer(page)
    return ("ok", summary, new_path)


def main():
    cfg_path = "config.json"
    total = 999
    for arg in sys.argv[1:]:
        if arg.isdigit():
            total = int(arg)
        else:
            cfg_path = arg

    cfg = load_config(cfg_path)
    log_path = cfg.get('realty_download_log', './logs/download_realty_log.json')
    dl_dir = cfg.get('download_temp', '/tmp/iros_pdf_downloads')
    save_dir = os.path.expanduser(
        cfg.get('realty_save_dir', '~/Downloads/부동산등기부등본')
    )

    log = load_log(log_path)

    os.makedirs(dl_dir, exist_ok=True)
    os.makedirs(save_dir, exist_ok=True)
    os.makedirs(os.path.dirname(log_path) or '.', exist_ok=True)

    print(f"건수: {total}, 이미완료: {len(log['completed'])}건")
    print(f"저장: {save_dir}")
    print("\n[사전 확인] TouchEn nxKey 보안 프로그램 설치 필수.\n")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            slow_mo=50,
            args=["--window-size=1400,900"],
            downloads_path=dl_dir,
        )
        ctx = browser.new_context(
            viewport={"width": 1400, "height": 900},
            locale="ko-KR",
            accept_downloads=True,
        )
        page = ctx.new_page()
        page.on("dialog", lambda d: d.accept())

        page.goto("https://www.iros.go.kr/index.jsp", wait_until="domcontentloaded", timeout=30000)

        print("=" * 50)
        print("  iros.go.kr 로그인 후 Enter")
        print("=" * 50)
        input(">>> ")

        # 부동산 신청결과 확인 페이지 이동
        print("신청결과(부동산) 확인 페이지 이동...")
        try:
            page.evaluate(f"""() => {{
                const el = document.getElementById('{BTN_MENU_REALTY_APPLY_RESULT}');
                if (el) el.click();
            }}""")
        except Exception:
            pass
        page.wait_for_timeout(4000)
        dismiss(page)

        if detect_security_install(page):
            print("\n[중단] TouchEn nxKey 보안 프로그램 설치 페이지 감지")
            print("  TouchEn nxKey 설치 후 브라우저 재시작 → 스크립트 재실행 필요")
            input(">>> Enter로 브라우저 닫기 ")
            browser.close()
            return

        ok, fail, done = 0, 0, 0
        consecutive_fails = 0
        start_index = len(log.get("completed", []))

        while done < total:
            done += 1
            idx = start_index + done
            print(f"[{done}] ", end="", flush=True)

            try:
                result = process_one(page, log, dl_dir, save_dir, idx)

                if result[0] == "no_more":
                    print("열람 버튼 없음 - 완료")
                    break
                elif result[0] == "ok":
                    _, summary, filepath = result
                    log["completed"].append({
                        "summary": summary,
                        "file": filepath,
                        "time": datetime.now().isoformat(),
                    })
                    ok += 1
                    consecutive_fails = 0
                else:
                    status = result[0]
                    summary = result[1] if len(result) > 1 else ""
                    log["failed"].append({
                        "summary": summary,
                        "reason": status,
                        "time": datetime.now().isoformat(),
                    })
                    fail += 1
                    consecutive_fails += 1

            except Exception as e:
                print(f"오류: {str(e)[:60]} X")
                log["failed"].append({
                    "summary": "",
                    "error": str(e)[:100],
                    "time": datetime.now().isoformat(),
                })
                fail += 1
                consecutive_fails += 1
                close_viewer(page)
                page.wait_for_timeout(2000)
                dismiss(page)

            # 연속 3회 실패 시 페이지 복구
            if consecutive_fails >= 3:
                print("\n  [경고] 연속 3회 실패 - 페이지 복구 중...")
                try:
                    page.evaluate(f"""() => {{
                        const el = document.getElementById('{BTN_MENU_REALTY_APPLY_RESULT}');
                        if (el) el.click();
                    }}""")
                    page.wait_for_timeout(4000)
                    dismiss(page)
                    consecutive_fails = 0
                except Exception:
                    pass

            if done % 5 == 0:
                save_log(log, log_path)

        save_log(log, log_path)

        print(f"\n{'='*50}")
        print(f"  완료! 성공:{ok} 실패:{fail}")
        print(f"  저장: {save_dir}")
        print(f"{'='*50}")
        input(">>> Enter로 브라우저 닫기 ")
        browser.close()


if __name__ == "__main__":
    main()

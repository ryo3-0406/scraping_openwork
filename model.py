import os
import tempfile
import streamlit as st
import pandas as pd
import undetected_chromedriver as uc
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def scrape_openwork(email: str, password: str, base_url: str) -> pd.DataFrame:
    # ——— ログファイル準備 ———
    log_file = os.path.join(tempfile.gettempdir(), "chromedriver.log")
    open(log_file, "w").close()

    # ——— ChromeOptions ———
    options = uc.ChromeOptions()
    options.headless = True                # 必ずヘッドレス
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--remote-debugging-port=9222")
    # Automation 検出回避
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    # ——— ドライバ起動 ———
    chromedriver_path = "/usr/bin/chromedriver"  # system-installed を使う
    service = Service(executable_path=chromedriver_path, log_path=log_file)
    driver = uc.Chrome(service=service, options=options)

    wait = WebDriverWait(driver, 10)
    results = []

    try:
        # ログイン
        driver.get("https://www.openwork.jp/login.php")
        wait.until(EC.presence_of_element_located((By.ID, "_username"))).send_keys(email)
        driver.find_element(By.ID, "_password").send_keys(password)
        driver.find_element(By.ID, "log_in").click()
        wait.until(EC.invisibility_of_element_located((By.ID, "log_in")))

        # ページめくりスクレイプ
        page = 1
        while True:
            url = base_url + (f"&next_page={page}" if page > 1 else "")
            driver.get(url)
            arts = wait.until(EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, "article.article, article.article-first")
            ))
            for art in arts:
                results.append({
                    "category": art.find_element(By.CSS_SELECTOR, "h3 a[title]").text.strip(),
                    "comment": art.find_element(By.CSS_SELECTOR, "dd.article_answer").text.strip()
                })
            # 次ページがなければループ終了
            if not driver.find_elements(By.CSS_SELECTOR, "a.paging_link-more"):
                break
            page += 1

    finally:
        driver.quit()
        # ログも Streamlit に出力しておく
        with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
            st.code(f.read(), language="text")

    return pd.DataFrame(results)

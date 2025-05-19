from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import chromedriver_autoinstaller

import pandas as pd
import os
import tempfile
import streamlit as st

def scrape_openwork(email: str, password: str, base_url: str, headless: bool = True) -> pd.DataFrame:
    """
    OpenWork の口コミページをログイン→全ページスクレイプし、
    DataFrameで返す。
    """
    log_file = os.path.join(tempfile.gettempdir(), "chromedriver.log")
    # 【１】事前に空ファイルを作っておく
    open(log_file, "w").close()

    # --- Selenium 動作設定 ---
    options = webdriver.ChromeOptions()
    # options = Options()
    options.binary_location = os.environ.get("CHROMIUM_PATH", "/usr/bin/chromium")

    # 1) 書き込み可能なディレクトリを作成
    install_dir = os.path.join(os.getcwd(), "chromedriver_bin")
    os.makedirs(install_dir, exist_ok=True)

    if headless:
        options.add_argument('--headless=new')

    # 共通オプション
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--lang=ja-JP')
    # （オプションでデバッグ用にリモートポートを開く）
    options.add_argument('--remote-debugging-port=9222')

    chromedriver_path = "/usr/bin/chromedriver"

    log_file = os.path.join(tempfile.gettempdir(), "chromedriver.log")

    service = Service(
        executable_path=chromedriver_path,
        log_path=log_file,
        service_args=["--verbose"]        # 追加
    )

    driver = webdriver.Chrome(service=service, options=options)

    wait = WebDriverWait(driver, 10)
    results = []

    try:
        # ログイン
        driver.get('https://www.openwork.jp/login.php')
        email_in = wait.until(EC.presence_of_element_located((By.ID, '_username')))
        email_in.clear(); email_in.send_keys(email)
        pw_in = driver.find_element(By.ID, '_password')
        pw_in.clear(); pw_in.send_keys(password)
        driver.find_element(By.ID, 'log_in').click()
        wait.until(EC.invisibility_of_element_located((By.NAME, 'login')))

        # ページめくりスクレイプ
        page = 1
        while True:
            url = f"{base_url}&next_page={page}" if page > 1 else base_url
            driver.get(url)
            try:
                wait.until(EC.presence_of_all_elements_located(
                    (By.CSS_SELECTOR, 'article.article, article.article-first')
                ))
            except TimeoutException:
                break

            for art in driver.find_elements(By.CSS_SELECTOR, 'article.article, article.article-first'):
                cat = art.find_element(By.CSS_SELECTOR, 'h3 a[title]').text.strip()
                com = art.find_element(By.CSS_SELECTOR, 'dd.article_answer').text.strip()
                results.append({'category': cat, 'comment': com})

            # 次ページリンクがなければ終了
            if not driver.find_elements(By.CSS_SELECTOR, 'a.paging_link-more'):
                break
            page += 1

    finally:
        driver.quit()
        # 【３】ファイルがあるかチェックしてから中身を Streamlit に出力
        if os.path.exists(log_file):
            with open(log_file, encoding="utf-8", errors="ignore") as f:
                log_text = f.read()
            # 長くなるので st.code か st.text_area で表示
            st.code(log_text, language="text")
        else:
            st.error(f"chromedriver.log が見つかりません: {log_file}")

    return pd.DataFrame(results)

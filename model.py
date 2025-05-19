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

def scrape_openwork(email: str, password: str, base_url: str, headless: bool = True) -> pd.DataFrame:
    """
    OpenWork の口コミページをログイン→全ページスクレイプし、
    DataFrameで返す。
    """
    # --- Selenium 動作設定 ---
    # options = webdriver.ChromeOptions()
    options = Options()
    options.binary_location = os.environ.get("CHROMIUM_PATH", "/usr/bin/chromium")

    # 1) 書き込み可能なディレクトリを作成
    install_dir = os.path.join(os.getcwd(), "chromedriver_bin")
    os.makedirs(install_dir, exist_ok=True)

    # 2) そのディレクトリにドライバをインストール
    #    戻り値はインストールされた chromedriver の絶対パス
    chromedriver_path = chromedriver_autoinstaller.install(path=install_dir)


    if headless:
        options.add_argument('--headless')

    # root や CI 環境向け安定化オプション
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--lang=ja-JP')

    # driver = webdriver.Chrome(
    #     service=ChromeService(ChromeDriverManager().install()),
    #     options=options
    # )

    # 3) Service にフルパスを渡して起動
    service = Service(executable_path=chromedriver_path)
    driver = webdriver.Chrome(service=service, options=options)

    # driver = webdriver.Chrome(service=Service(), options=options)

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

    return pd.DataFrame(results)

import os
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# 環境変数から読み込み
EMAIL = os.getenv('OPENWORK_EMAIL')
PASSWORD = os.getenv('OPENWORK_PASSWORD')
COMPANY_M_ID = os.getenv('COMPANY_M_ID', 'a0910000000FqfX')

if not EMAIL or not PASSWORD:
    raise ValueError("環境変数 OPENWORK_EMAIL と OPENWORK_PASSWORD を設定してください。")

# --- 1. ChromeOptions の設定 ---
options = webdriver.ChromeOptions()
# システムにインストールされた Chromium を指定
options.binary_location = os.getenv('CHROME_BINARY', '/usr/bin/chromium-browser')
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--disable-gpu')
options.add_argument('--window-size=1920,1080')
options.add_argument('--lang=ja-JP')

# システムの chromedriver を使う
chromedriver_path = os.getenv('CHROMEDRIVER_PATH', '/usr/bin/chromedriver')
service = ChromeService(chromedriver_path)

driver = webdriver.Chrome(service=service, options=options)
wait = WebDriverWait(driver, 15)
results = []

try:
    # --- 2. ログイン ---
    login_url = 'https://www.openwork.jp/login.php'
    driver.get(login_url)
    # ページがJSで描画されるまで少し待つ（場合によっては不要）
    # wait.until(EC.presence_of_element_located((By.TAG_NAME, 'body')))

    # ID・PW フォームはJSで動的生成されるため、iframeがある場合はそちらを切り替えるなどの対応が必要です。
    # ここでは例としてフォーム要素を直接操作します。
    email_input = wait.until(EC.presence_of_element_located((By.ID, '_username')))
    email_input.clear()
    email_input.send_keys(EMAIL)
    pwd_input = driver.find_element(By.ID, '_password')
    pwd_input.clear()
    pwd_input.send_keys(PASSWORD)
    driver.find_element(By.ID, 'log_in').click()
    # ログインフォームが消えるまで待機
    wait.until(EC.invisibility_of_element_located((By.NAME, 'login')))

    # --- 3. ページネーション付きスクレイピング ---
    page = 1
    base_url = f'https://www.openwork.jp/company_answer.php?m_id={COMPANY_M_ID}'
    while True:
        url = base_url + (f'&next_page={page}' if page > 1 else '')
        driver.get(url)
        try:
            wait.until(EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, 'article.article, article.article-first')
            ))
        except TimeoutException:
            print(f"ページ {page} の記事要素が見つからず終了: {url}")
            break

        articles = driver.find_elements(By.CSS_SELECTOR, 'article.article, article.article-first')
        for art in articles:
            cat_el = art.find_element(By.CSS_SELECTOR, 'h3 a[title]')
            com_el = art.find_element(By.CSS_SELECTOR, 'dd.article_answer')
            results.append({
                'カテゴリ': cat_el.text.strip(),
                'コメント': com_el.text.strip()
            })

        # 「もっと見る」リンクがなければ終了
        if not driver.find_elements(By.CSS_SELECTOR, 'a.paging_link-more'):
            print(f"全 {page} ページを処理し、合計 {len(results)} 件取得しました。")
            break
        page += 1

finally:
    driver.quit()

# --- 4. DataFrame化 & Excel出力 ---
df = pd.DataFrame(results)
output_path = 'openwork_comments.xlsx'
df.to_excel(output_path, index=False)
print(f'Excelファイルを出力しました: {output_path}')

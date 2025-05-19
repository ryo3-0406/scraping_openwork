import requests
from bs4 import BeautifulSoup
import pandas as pd

def scrape_openwork(email: str, password: str, base_url: str) -> pd.DataFrame:
    """
    OpenWork の口コミページをログイン→全ページスクレイプし、DataFrameで返す。
    Selenium は使わずに requests＋BeautifulSoup で実装します。
    """
    session = requests.Session()
    login_url = "https://www.openwork.jp/login.php"

    # 1) ログインページを GET して hidden フィールドを拾う
    r = session.get(login_url)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    form = soup.find("form")
    payload = {
        inp["name"]: inp.get("value", "")
        for inp in form.find_all("input", {"name": True})
    }

    # 2) メール・パスワードをセットして POST
    payload["_username"] = email
    payload["_password"] = password
    payload["log_in"] = form.find("button", {"id": "log_in"}).get_text(strip=True)
    r = session.post(login_url, data=payload)
    r.raise_for_status()

    # 3) ログイン成功チェック（ログイン後も login.php に留まっていたら失敗）
    if "login.php" in r.url:
        raise RuntimeError("ログインに失敗しました。メールアドレス／パスワードを確認してください。")

    # 4) レビューをページめくりで取得
    results = []
    page = 1
    while True:
        url = base_url + (f"&next_page={page}" if page > 1 else "")
        r = session.get(url)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        articles = soup.select("article.article, article.article-first")
        if not articles:
            break

        for art in articles:
            cat_el = art.select_one("h3 a[title]")
            com_el = art.select_one("dd.article_answer")
            if cat_el and com_el:
                results.append({
                    "category": cat_el.get_text(strip=True),
                    "comment": com_el.get_text(strip=True)
                })

        # 「もっと見る」リンクがなければ終了
        if not soup.select_one("a.paging_link-more"):
            break
        page += 1

    return pd.DataFrame(results)

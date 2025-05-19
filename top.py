import io
import streamlit as st
from model import scrape_openwork

st.set_page_config(page_title="OpenWork 口コミダウンロード", layout="wide")

st.title("OpenWork 口コミダウンロード app")

# --- 入力フォーム ---
email = st.text_input("メールアドレス", type="default")
password = st.text_input("パスワード", type="password")
base_url = st.text_input("会社の口コミページURL",
    value="https://www.openwork.jp/company_answer.php?m_id=a0910000000FqfX")

if st.button("口コミを取得してExcelダウンロード"):
    if not (email and password and base_url):
        st.error("メール・パスワード・URL をすべて入力してください。")
    else:
        with st.spinner("スクレイピング中…しばらくお待ちください"):
            try:
                df = scrape_openwork(email, password, base_url, headless=False)
            except Exception as e:
                st.error(f"エラーが発生しました: {e}")
            else:
                if df.empty:
                    st.warning("口コミが見つかりませんでした。URLやログイン情報を確認してください。")
                else:
                    st.success(f"{len(df)} 件の口コミを取得しました。")
                    st.dataframe(df)

                    # Excel バッファ作成
                    towrite = io.BytesIO()
                    df.to_excel(towrite, index=False, sheet_name="Reviews")
                    towrite.seek(0)

                    st.download_button(
                        label="Excel ファイルをダウンロード",
                        data=towrite,
                        file_name="openwork_comments.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

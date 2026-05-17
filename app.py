import streamlit as st
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
from google import genai

# --- Googleスプレッドシートに接続するための設定 ---
def get_google_sheet():
    # アクセス権限の範囲を指定
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    # 先ほど配置した JSON ファイルを使って認証
    creds = Credentials.from_service_account_file("google_key.json", scopes=scopes)
    client = gspread.authorize(creds)
    
    # 作成したスプレッドシートの名前を指定して開く
    # (最初のシート「シート1」を取得)
    sheet = client.open("AI_Diary_Data").sheet1
    return sheet

def save_to_google_sheet(date, content, feedback):
    sheet = get_google_sheet()
    # 新しい行として [日付, 本文, AI評価] を追加
    sheet.append_row([date, content, feedback])

def load_from_google_sheet():
    try:
        sheet = get_google_sheet()
        all_values = sheet.get_all_values()
        
        # データが1行（見出しだけ）以下の場合は空のリストを返す
        if len(all_values) <= 1:
            return []
            
        # 1行目の見出し(date, content, feedback)を除外し、新しい順(逆順)にする
        return all_values[1:][::-1]
    except Exception as e:
        st.error(f"データの読み込みに失敗しました: {e}")
        return []

# --- 画面構成 ---
st.set_page_config(page_title="AI日記アプリ", layout="centered")
st.title("📖 AIフィードバック日記")

# .streamlit/secrets.toml からAPIキーを自動読み込み
api_key = st.secrets["GEMINI_API_KEY"]

st.subheader("今日のできごと")
diary_content = st.text_area("短い日記を書いてみましょう", height=150)

if st.button("日記を保存してAIに評価してもらう"):
    if diary_content:
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        with st.spinner("Geminiが日記を読んでいます..."):
            try:
                # Gemini APIの呼び出し
                client = genai.Client(api_key=api_key)
                prompt = f"あなたは優しい日記アドバイザーです。次の短い日記を読んで、良かった点や前向きになれるアドバイスを2文以内で回答し、最後に改行して5段階の星評価（例：⭐⭐⭐⭐）をつけてください。\n\n【日記】\n{diary_content}"
                
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt,
                )
                ai_feedback = response.text

                # --- 変更点：Googleスプレッドシートに保存 ---
                save_to_google_sheet(now, diary_content, ai_feedback)
                st.success("日記をGoogleスプレッドシートに保存しました！")
                st.rerun()

            except Exception as e:
                st.error(f"エラーが発生しました: {e}")
    else:
        st.warning("日記の文章を入力してください。")

st.divider()
st.subheader("過去の記録")

# --- 変更点：Googleスプレッドシートから履歴を読み込んで表示 ---
with st.spinner("履歴を読み込み中..."):
    history = load_from_google_sheet()

if history:
    for entry in history:
        with st.expander(f"📅 {entry[0]}"):
            st.write(f"📝 {entry[1]}")
            st.info(entry[2])
else:
    st.info("過去の記録はまだありません。")
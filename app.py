import streamlit as st
from st_supabase_connection import SupabaseConnection
import random

# 1. ページ設定
st.set_page_config(page_title="Focus Enemy", page_icon="⚔️")
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Press+Start+2P&display=swap');
    html, body, [class*="css"]  {
        font-family: 'Press+Start+2P', cursive;
    }
    .stButton>button { width: 100%; border: 3px solid #e94560; }
    </style>
    """, unsafe_allow_html=True)

# 2. 【重要】Secretsを使わず直接接続情報を指定
# 以下の値はあなたが教えてくれた正しい値です
SUPABASE_URL = "https://fxzrckbhxqsdslrapmav.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZ4enJja2JoeHFzZHNscmFwbWF2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzAwMzY4MjYsImV4cCI6MjA4NTYxMjgyNn0.9RNZWdD09IeEiM3O4ji6CyXufMoGi3UzqmKjAkr93sc"

# 直接引数で渡すことで、Secretsの設定ミスを回避します
conn = st.connection("supabase", type=SupabaseConnection, url=SUPABASE_URL, key=SUPABASE_KEY)

# --- 以下、ロジック部分は変更なし ---
if 'enemy_hp' not in st.session_state:
    st.session_state.enemy_hp = 100
if 'current_word' not in st.session_state:
    st.session_state.current_word = None

def fetch_new_word():
    try:
        res = conn.table("words").select("*").order("miss_count", desc=True).limit(10).execute()
        if res.data:
            st.session_state.current_word = random.choice(res.data)
    except Exception:
        st.error("Supabaseのテーブル 'words' が見つからないか、データがありません。SQL Editorでテーブル作成とデータ挿入を行ってください。")

if st.session_state.current_word is None:
    fetch_new_word()

st.title("⚔️ FOCUS ENEMY")
if st.session_state.current_word:
    st.subheader(f"TARGET: {st.session_state.current_word['word']}")
    st.progress(st.session_state.enemy_hp / 100)
    st.write(f"ENEMY HP: {st.session_state.enemy_hp}%")

    options = [st.session_state.current_word['meaning'], "本", "車", "猫", "太陽"]
    random.shuffle(options)

    cols = st.columns(2)
    for i, opt in enumerate(options):
        with cols[i % 2]:
            if st.button(opt, key=f"btn_{i}"):
                if opt == st.session_state.current_word['meaning']:
                    st.success("HIT!")
                    st.session_state.enemy_hp -= 25
                    conn.table("words").update({"correct_count": st.session_state.current_word['correct_count'] + 1}).eq("id", st.session_state.current_word['id']).execute()
                else:
                    st.error("MISS!")
                    conn.table("words").update({"miss_count": st.session_state.current_word['miss_count'] + 1}).eq("id", st.session_state.current_word['id']).execute()
                
                if st.session_state.enemy_hp <= 0:
                    st.balloons()
                    st.session_state.enemy_hp = 100
                
                fetch_new_word()
                st.rerun()
else:
    st.warning("単語をロード中、またはデータがありません。")

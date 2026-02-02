import streamlit as st
from st_supabase_connection import SupabaseConnection
import pandas as pd
import random
import re

# 1. ページ設定とデザイン（カラーテーマの刷新）
st.set_page_config(page_title="Word Dungeon", page_icon="🏰", layout="wide")
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@700&display=swap');
    
    html, body, [class*="css"]  {
        font-family: 'Noto Sans JP', sans-serif;
        background-color: #0f172a; /* 深みのあるネイビー */
        color: #f8fafc;
    }
    /* ボタンを清潔感のあるブルーに変更 */
    .stButton>button { 
        width: 100%; 
        border: none; 
        height: 60px; 
        background-color: #3b82f6; 
        color: white; 
        border-radius: 8px;
        font-weight: bold;
        transition: 0.3s;
    }
    .stButton>button:hover { 
        background-color: #2563eb; 
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.4);
    }
    .main-box { 
        background-color: #1e293b; 
        padding: 25px; 
        border-radius: 15px; 
        border: 1px solid #334155; 
    }
    </style>
    """, unsafe_allow_html=True)

# 2. 直接接続
SUPABASE_URL = "https://fxzrckbhxqsdslrapmav.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZ4enJja2JoeHFzZHNscmFwbWF2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzAwMzY4MjYsImV4cCI6MjA4NTYxMjgyNn0.9RNZWdD09IeEiM3O4ji6CyXufMoGi3UzqmKjAkr93sc"
conn = st.connection("supabase", type=SupabaseConnection, url=SUPABASE_URL, key=SUPABASE_KEY)

# 判定を確実に通すための洗浄関数
def clean_text(text):
    if not text: return ""
    # 正規表現で「文字と数字以外」をすべて削除し、空白も詰める
    return re.sub(r'[^\w\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]', '', str(text))

# 状態管理
if 'game_started' not in st.session_state: st.session_state.game_started = False
if 'enemy_hp' not in st.session_state: st.session_state.enemy_hp = 100
if 'player_hp' not in st.session_state: st.session_state.player_hp = 100
if 'current_word' not in st.session_state: st.session_state.current_word = None
if 'last_result' not in st.session_state: st.session_state.last_result = None

def fetch_new_word():
    res = conn.table("words").select("*").order("miss_count", desc=True).limit(20).execute()
    if res.data:
        st.session_state.current_word = random.choice(res.data)
        st.session_state.enemy_hp = 100

# --- スタート画面 ---
if not st.session_state.game_started:
    st.title("🏰 WORD DUNGEON")
    st.write("落ち着いた環境で、着実に語彙力を鍛えよう。")
    if st.button("🔥 探索を開始する"):
        st.session_state.game_started = True
        st.session_state.player_hp = 100
        st.session_state.last_result = None
        fetch_new_word()
        st.rerun()
    
    if st.button("♻️ 全戦績リセット"):
        conn.table("words").update({"correct_count": 0, "miss_count": 0}).neq("word", "").execute()
        st.success("リセット完了")
    st.stop()

# --- バトル画面 ---
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown('<div class="main-box">', unsafe_allow_html=True)
    st.write(f"❤️ あなたの体力: {st.session_state.player_hp}%")
    st.progress(max(0, st.session_state.player_hp) / 100)
    
    if st.session_state.current_word:
        m_count = st.session_state.current_word['miss_count']
        rank = "[ラスボス]" if m_count >= 10 else "[中ボス]" if m_count >= 5 else "[雑魚]"
        
        st.subheader(f"{rank} {st.session_state.current_word['word']}")
        st.write(f"👾 敵の体力: {st.session_state.enemy_hp}%")
        st.progress(max(0, st.session_state.enemy_hp) / 100)

        if st.session_state.last_result:
            st.info(st.session_state.last_result)

        # 判定強化
        correct_raw = st.session_state.current_word['meaning']
        correct_clean = clean_text(correct_raw)
        
        # 選択肢
        options = list(set([correct_raw, "りんご", "本", "車", "猫", "太陽", "月", "空"]))
        final_options = random.sample([o for o in options if clean_text(o) != correct_clean], 3) + [correct_raw]
        random.shuffle(final_options)

        cols = st.columns(2)
        for i, opt in enumerate(final_options):
            with cols[i % 2]:
                if st.button(opt, key=f"btn_{i}"):
                    if clean_text(opt) == correct_clean:
                        st.session_state.enemy_hp -= 34
                        st.session_state.last_result = f"✅ 正解！ {st.session_state.current_word['word']} = {correct_raw}"
                        conn.table("words").update({"correct_count": st.session_state.current_word['correct_count'] + 1}).eq("id", st.session_state.current_word['id']).execute()
                        if st.session_state.enemy_hp <= 0:
                            st.balloons()
                            fetch_new_word()
                    else:
                        st.session_state.player_hp -= 20
                        st.session_state.last_result = f"❌ 間違い！ 正解は「{correct_raw}」"
                        conn.table("words").update({"miss_count": st.session_state.current_word['miss_count'] + 1}).eq("id", st.session_state.current_word['id']).execute()
                    
                    if st.session_state.player_hp <= 0:
                        st.session_state.game_started = False
                    st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    if st.button("🏃 拠点へ戻る"):
        st.session_state.game_started = False
        st.rerun()

with col2:
    st.subheader("📊 討伐表")
    res_all = conn.table("words").select("*").execute()
    if res_all.data:
        df = pd.DataFrame(res_all.data)
        st.dataframe(df[['word', 'miss_count']].sort_values('miss_count', ascending=False), hide_index=True)

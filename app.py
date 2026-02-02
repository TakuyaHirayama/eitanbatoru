import streamlit as st
from st_supabase_connection import SupabaseConnection
import pandas as pd
import random

# 1. ページ設定とデザイン
st.set_page_config(page_title="Focus Enemy", page_icon="⚔️", layout="wide")
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Press+Start+2P&display=swap');
    html, body, [class*="css"]  {
        font-family: 'Press+Start+2P', cursive;
    }
    .stButton>button { width: 100%; border: 3px solid #e94560; height: 60px; font-size: 14px; }
    .main-box { background-color: #1a1a2e; padding: 20px; border-radius: 10px; border: 2px solid #fff; }
    </style>
    """, unsafe_allow_html=True)

# 2. 直接接続（Secretsエラー回避用）
SUPABASE_URL = "https://fxzrckbhxqsdslrapmav.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZ4enJja2JoeHFzZHNscmFwbWF2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzAwMzY4MjYsImV4cCI6MjA4NTYxMjgyNn0.9RNZWdD09IeEiM3O4ji6CyXufMoGi3UzqmKjAkr93sc"
conn = st.connection("supabase", type=SupabaseConnection, url=SUPABASE_URL, key=SUPABASE_KEY)

# 状態管理
if 'enemy_hp' not in st.session_state: st.session_state.enemy_hp = 100
if 'current_word' not in st.session_state: st.session_state.current_word = None
if 'last_result' not in st.session_state: st.session_state.last_result = None

def fetch_new_word():
    res = conn.table("words").select("*").order("miss_count", desc=True).limit(10).execute()
    if res.data:
        st.session_state.current_word = random.choice(res.data)

if st.session_state.current_word is None:
    fetch_new_word()

# --- メインゲーム画面 ---
st.title("⚔️ FOCUS ENEMY")
st.write("苦手な単語ほど敵として出現しやすいぞ！")

col1, col2 = st.columns([2, 1])

with col1:
    st.markdown('<div class="main-box">', unsafe_allow_html=True)
    if st.session_state.current_word:
        st.header(f"TARGET: {st.session_state.current_word['word']}")
        st.progress(st.session_state.enemy_hp / 100)
        st.write(f"ENEMY HP: {st.session_state.enemy_hp}%")

        # 前回の答えを表示（答え合わせ機能）
        if st.session_state.last_result:
            st.info(st.session_state.last_result)

        # 選択肢の作成
        options = [st.session_state.current_word['meaning'], "本", "車", "猫", "太陽"]
        random.shuffle(options)

        cols = st.columns(2)
        for i, opt in enumerate(options):
            with cols[i % 2]:
                if st.button(opt, key=f"btn_{i}"):
                    correct_ans = st.session_state.current_word['meaning']
                    if opt == correct_ans:
                        st.session_state.enemy_hp -= 25
                        st.session_state.last_result = f"⭕ 正解！ 「{st.session_state.current_word['word']}」＝「{correct_ans}」"
                        conn.table("words").update({"correct_count": st.session_state.current_word['correct_count'] + 1}).eq("id", st.session_state.current_word['id']).execute()
                    else:
                        st.session_state.last_result = f"❌ 不正解！ 正解は 「{st.session_state.current_word['word']}」＝「{correct_ans}」 でした。"
                        conn.table("words").update({"miss_count": st.session_state.current_word['miss_count'] + 1}).eq("id", st.session_state.current_word['id']).execute()
                    
                    if st.session_state.enemy_hp <= 0:
                        st.balloons()
                        st.session_state.enemy_hp = 100
                    
                    fetch_new_word()
                    st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# --- 成績一覧セクション ---
st.divider()
st.header("📊 あなたの戦績（正答率一覧）")
res_all = conn.table("words").select("*").execute()
if res_all.data:
    df = pd.DataFrame(res_all.data)
    # 正答率の計算
    df['total'] = df['correct_count'] + df['miss_count']
    df['正答率'] = df.apply(lambda x: f"{(x['correct_count']/x['total']*100):.1f}%" if x['total'] > 0 else "0%", axis=1)
    
    # 表示用の整形
    display_df = df[['word', 'meaning', 'correct_count', 'miss_count', '正答率']].sort_values('miss_count', ascending=False)
    display_df.columns = ['英単語', '意味', '正解数', 'ミス数', '現在の正答率']
    
    st.table(display_df)

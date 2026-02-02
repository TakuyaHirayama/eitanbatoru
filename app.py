import streamlit as st
from st_supabase_connection import SupabaseConnection
import pandas as pd
import random

# 1. デザイン設定（ネオンとアニメーション）
st.set_page_config(page_title="Word Dungeon: Ultra Combo", page_icon="🔥", layout="wide")
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@900&family=Black+Ops+One&display=swap');
    
    html, body, [class*="css"] { 
        font-family: 'Inter', sans-serif; background-color: #020617; color: #f1f5f9; 
    }
    
    /* ボタンデザイン */
    .stButton>button { 
        width: 100%; border-radius: 20px; height: 75px; font-weight: 900; font-size: 1.3rem;
        background: linear-gradient(45deg, #1e40af 0%, #3b82f6 100%);
        color: white; border: 2px solid #60a5fa; transition: 0.1s;
    }
    .stButton>button:hover { transform: scale(1.02); box-shadow: 0 0 25px rgba(59, 130, 246, 0.5); }
    
    /* コンボ・正誤演出 */
    .combo-text { font-family: 'Black Ops One', cursive; color: #fbbf24; font-size: 3.5rem; text-shadow: 0 0 20px #d97706; }
    .correct-text { color: #10b981; font-family: 'Orbitron'; font-size: 2.5rem; font-weight: 900; }
    .miss-text { color: #ef4444; font-family: 'Orbitron'; font-size: 2rem; font-weight: 900; }
    .answer-text { color: #f8fafc; background: #ef4444; padding: 5px 15px; border-radius: 10px; font-size: 1.5rem; }
    
    .status-card { 
        background: rgba(30, 41, 59, 0.8); padding: 35px; border-radius: 28px; 
        border: 2px solid #334155; text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. Supabase接続
SUPABASE_URL = "https://fxzrckbhxqsdslrapmav.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZ4enJja2JoeHFzZHNscmFwbWF2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzAwMzY4MjYsImV4cCI6MjA4NTYxMjgyNn0.9RNZWdD09IeEiM3O4ji6CyXufMoGi3UzqmKjAkr93sc"
conn = st.connection("supabase", type=SupabaseConnection, url=SUPABASE_URL, key=SUPABASE_KEY)

# 3. 状態管理
if 'game_started' not in st.session_state: st.session_state.game_started = False
if 'player_hp' not in st.session_state: st.session_state.player_hp = 100
if 'combo' not in st.session_state: st.session_state.combo = 0
if 'current_word' not in st.session_state: st.session_state.current_word = None
if 'choices' not in st.session_state: st.session_state.choices = []
if 'last_feedback' not in st.session_state: st.session_state.last_feedback = None # ⭕/❌表示用
if 'session_missed' not in st.session_state: st.session_state.session_missed = []
if 'show_result' not in st.session_state: st.session_state.show_result = False

def fetch_new_word():
    res = conn.table("words").select("*").order("miss_count", desc=True).limit(25).execute()
    if res.data:
        word_data = random.choice(res.data)
        st.session_state.current_word = word_data
        correct_id = word_data['id']
        all_words = conn.table("words").select("id, meaning").limit(40).execute().data
        dummies = [w for w in all_words if w['id'] != correct_id]
        raw_choices = random.sample(dummies, 3) + [{'id': correct_id, 'meaning': word_data['meaning']}]
        random.shuffle(raw_choices)
        st.session_state.choices = raw_choices

# --- メインロジック ---
tab1, tab2 = st.tabs(["⚔️ DUNGEON", "⚙️ SYSTEM"])

with tab1:
    if st.session_state.show_result:
        st.markdown('<div class="status-card">', unsafe_allow_html=True)
        score = st.session_state.combo # 最高記録などを出しても良い
        st.markdown(f"<h1 style='font-size:80px; color:#fbbf24;'>FINISH!</h1>", unsafe_allow_html=True)
        if st.session_state.session_missed:
            st.write("### 復習リスト")
            st.table(pd.DataFrame(st.session_state.session_missed).drop_duplicates())
        if st.button("再挑戦する"):
            st.session_state.show_result = False
            st.session_state.combo = 0
            st.session_state.session_missed = []
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    elif not st.session_state.game_started:
        st.title("🛡️ WORD DUNGEON ULTRA")
        if st.button("🔥 潜入開始"):
            st.session_state.game_started = True
            st.session_state.player_hp = 100
            st.session_state.combo = 0
            st.session_state.last_feedback = None
            fetch_new_word()
            st.rerun()

    else:
        st.markdown('<div class="status-card">', unsafe_allow_html=True)
        
        # コンボ表示
        if st.session_state.combo > 0:
            st.markdown(f'<div class="combo-text">{st.session_state.combo} COMBO!</div>', unsafe_allow_html=True)

        # 直前のフィードバック演出
        if st.session_state.last_feedback == "correct":
            st.markdown('<div class="correct-text">⭕ PERFECT!</div>', unsafe_allow_html=True)
        elif st.session_state.last_feedback == "miss":
            st.markdown(f'<div class="miss-text">❌ MISS...</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="answer-text">正解は: {st.session_state.prev_answer}</div>', unsafe_allow_html=True)
        
        st.metric("YOUR HP", f"{st.session_state.player_hp}%")
        
        word_data = st.session_state.current_word
        st.markdown(f"<h1 style='font-size:3.5rem; color:#60a5fa;'>{word_data['word']}</h1>", unsafe_allow_html=True)
        
        cols = st.columns(2)
        for i, choice in enumerate(st.session_state.choices):
            with cols[i % 2]:
                if st.button(choice['meaning'], key=f"btn_{i}"):
                    # 判定
                    if choice['id'] == word_data['id']:
                        st.session_state.last_feedback = "correct"
                        st.session_state.combo += 1
                        conn.table("words").update({"correct_count": word_data['correct_count'] + 1}).eq("id", word_data['id']).execute()
                    else:
                        st.session_state.last_feedback = "miss"
                        st.session_state.prev_answer = word_data['meaning'] # 答えを保存
                        st.session_state.combo = 0 # コンボリセット
                        st.session_state.player_hp -= 25
                        st.session_state.session_missed.append({"英単語": word_data['word'], "意味": word_data['meaning']})
                        conn.table("words").update({"miss_count": word_data['miss_count'] + 1}).eq("id", word_data['id']).execute()
                    
                    if st.session_state.player_hp <= 0:
                        st.session_state.game_started = False
                        st.session_state.show_result = True
                    else:
                        fetch_new_word()
                    st.rerun()
        
        st.divider()
        if st.button("🏃 拠点へ戻る"):
            st.session_state.game_started = False
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

with tab2:
    st.header("⚙️ 管理画面")
    if st.button("📦 必須単語をロード"):
        samples = [{"word": "Reluctant", "meaning": "気が進まない"}, {"word": "Submit", "meaning": "提出する"}]
        for s in samples: conn.table("words").insert(s).execute()
        st.success("完了")

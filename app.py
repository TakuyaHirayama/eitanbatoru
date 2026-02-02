import streamlit as st
from st_supabase_connection import SupabaseConnection
import pandas as pd
import random
import time

# 1. ページ設定と超豪華デザイン
st.set_page_config(page_title="Word Dungeon: Ultimate", page_icon="⚔️", layout="wide")
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;900&family=Noto+Sans+JP:wght@900&display=swap');
    
    html, body, [class*="css"] { 
        font-family: 'Inter', sans-serif; 
        background-color: #020617; 
        color: #f1f5f9; 
    }
    
    .stButton>button { 
        width: 100%; border-radius: 20px; height: 70px; font-weight: 900; font-size: 1.2rem;
        background: linear-gradient(45deg, #1e40af 0%, #3b82f6 100%);
        color: white; border: 2px solid #60a5fa; transition: 0.2s;
        text-transform: uppercase; letter-spacing: 1px;
    }
    .stButton>button:hover { transform: translateY(-3px); box-shadow: 0 0 30px rgba(59, 130, 246, 0.6); border-color: white; }
    
    .status-card { 
        background: rgba(30, 41, 59, 0.7); padding: 30px; border-radius: 24px; 
        border: 1px solid #334155; backdrop-filter: blur(10px); text-align: center;
    }
    
    .effect-correct { color: #10b981; font-family: 'Orbitron'; font-size: 3rem; font-weight: 900; animation: blink 0.5s ease-in-out; }
    .effect-miss { color: #ef4444; font-family: 'Orbitron'; font-size: 3rem; font-weight: 900; animation: blink 0.5s ease-in-out; }
    
    @keyframes blink { 0% { opacity: 0; transform: scale(0.5); } 50% { opacity: 1; transform: scale(1.1); } 100% { opacity: 1; transform: scale(1); } }
    </style>
    """, unsafe_allow_html=True)

# 2. Supabase接続
SUPABASE_URL = "https://fxzrckbhxqsdslrapmav.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZ4enJja2JoeHFzZHNscmFwbWF2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzAwMzY4MjYsImV4cCI6MjA4NTYxMjgyNn0.9RNZWdD09IeEiM3O4ji6CyXufMoGi3UzqmKjAkr93sc"
conn = st.connection("supabase", type=SupabaseConnection, url=SUPABASE_URL, key=SUPABASE_KEY)

# 3. 状態管理
if 'game_started' not in st.session_state: st.session_state.game_started = False
if 'enemy_hp' not in st.session_state: st.session_state.enemy_hp = 100
if 'player_hp' not in st.session_state: st.session_state.player_hp = 100
if 'current_word' not in st.session_state: st.session_state.current_word = None
if 'choices' not in st.session_state: st.session_state.choices = []
if 'session_score' not in st.session_state: st.session_state.session_score = 0
if 'session_missed' not in st.session_state: st.session_state.session_missed = []
if 'show_result' not in st.session_state: st.session_state.show_result = False
if 'last_feedback' not in st.session_state: st.session_state.last_feedback = ""

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

# --- UIセクション ---
tab1, tab2 = st.tabs(["⚔️ BATTLE", "⚙️ SYSTEM"])

with tab1:
    # A. リザルト画面
    if st.session_state.show_result:
        st.markdown('<div class="status-card">', unsafe_allow_html=True)
        score = st.session_state.session_score
        rank = "S" if score >= 15 else "A" if score >= 10 else "B"
        st.markdown(f"<h1 style='font-size:100px; color:#fbbf24;'>{rank}</h1>", unsafe_allow_html=True)
        st.subheader(f"討伐スコア: {score}")
        if st.session_state.session_missed:
            st.write("### 復習が必要な魔物たち")
            st.table(pd.DataFrame(st.session_state.session_missed).drop_duplicates())
        if st.button("再出撃する"):
            st.session_state.show_result = False
            st.session_state.session_score = 0
            st.session_state.session_missed = []
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # B. スタート画面
    elif not st.session_state.game_started:
        st.title("🛡️ WORD DUNGEON ULTIMATE")
        col_start, _ = st.columns([1, 2])
        with col_start:
            if st.button("🔥 潜入開始"):
                st.session_state.game_started = True
                st.session_state.player_hp = 100
                st.session_state.enemy_hp = 100
                st.session_state.last_feedback = ""
                fetch_new_word()
                st.rerun()

    # C. バトル画面
    else:
        st.markdown('<div class="status-card">', unsafe_allow_html=True)
        
        # 巨大フィードバック演出（ここが新しい！）
        if st.session_state.last_feedback == "correct":
            st.markdown('<div class="effect-correct">⭕ EXCELLENT!</div>', unsafe_allow_html=True)
        elif st.session_state.last_feedback == "miss":
            st.markdown('<div class="effect-miss">❌ DAMAGED!</div>', unsafe_allow_html=True)
        
        # HPバー
        c1, c2 = st.columns(2)
        c1.metric("YOUR HP", f"{st.session_state.player_hp}%")
        c2.metric("DUNGEON HP", f"{st.session_state.enemy_hp}%")
        
        word_data = st.session_state.current_word
        st.markdown(f"<h1 style='font-size:4rem; color:#60a5fa;'>{word_data['word']}</h1>", unsafe_allow_html=True)
        
        cols = st.columns(2)
        for i, choice in enumerate(st.session_state.choices):
            with cols[i % 2]:
                if st.button(choice['meaning'], key=f"btn_{i}"):
                    if choice['id'] == word_data['id']:
                        st.session_state.last_feedback = "correct"
                        st.session_state.session_score += 1
                        st.session_state.enemy_hp -= 10
                        conn.table("words").update({"correct_count": word_data['correct_count'] + 1}).eq("id", word_data['id']).execute()
                    else:
                        st.session_state.last_feedback = "miss"
                        st.session_state.player_hp -= 20
                        st.session_state.session_missed.append({"英単語": word_data['word'], "意味": word_data['meaning']})
                        conn.table("words").update({"miss_count": word_data['miss_count'] + 1}).eq("id", word_data['id']).execute()
                    
                    if st.session_state.player_hp <= 0 or st.session_state.enemy_hp <= 0:
                        st.session_state.game_started = False
                        st.session_state.show_result = True
                    else:
                        fetch_new_word()
                    st.rerun()
        
        st.divider()
        if st.button("🏃 拠点へ帰還する"):
            st.session_state.game_started = False
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

with tab2:
    st.header("⚙️ システム設定")
    if st.button("📦 必須単語セットをインストール"):
        samples = [{"word": "Reluctant", "meaning": "気が進まない"}, {"word": "Persistent", "meaning": "粘り強い"}, {"word": "Meticulous", "meaning": "細心の注意を払った"}]
        for s in samples: conn.table("words").insert(s).execute()
        st.success("単語セットをロードしました。")
    
    with st.form("manual"):
        w = st.text_input("英単語")
        m = st.text_input("意味")
        if st.form_submit_button("単語を追加"):
            conn.table("words").insert({"word": w, "meaning": m}).execute()
            st.success("追加完了")

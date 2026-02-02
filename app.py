import streamlit as st
from st_supabase_connection import SupabaseConnection
import pandas as pd
import random

# 1. デザイン設定
st.set_page_config(page_title="Word Dungeon: Pro", page_icon="⚔️", layout="wide")
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700&family=Noto+Sans+JP:wght@900&display=swap');
    
    html, body, [class*="css"] { 
        font-family: 'Inter', 'Noto Sans JP', sans-serif; background-color: #020617; color: #f1f5f9; 
    }
    
    .stButton>button { 
        width: 100%; border-radius: 16px; height: 70px; font-weight: 700;
        background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%);
        color: white; border: 1px solid #60a5fa;
    }
    
    /* コンボ：光を抑えて視認性重視 */
    .combo-text { font-family: 'Orbitron'; color: #fbbf24; font-size: 2.5rem; font-weight: 900; text-shadow: 2px 2px 4px #000; }
    
    /* ダメージ演出 */
    .dmg-give { color: #10b981; font-weight: 900; font-size: 1.5rem; }
    .dmg-take { color: #ef4444; font-weight: 900; font-size: 1.5rem; }
    
    .status-card { 
        background: #1e293b; padding: 25px; border-radius: 20px; border: 1px solid #334155; text-align: center;
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
if 'enemy_hp' not in st.session_state: st.session_state.enemy_hp = 100
if 'combo' not in st.session_state: st.session_state.combo = 0
if 'max_combo' not in st.session_state: st.session_state.max_combo = 0
if 'kill_count' not in st.session_state: st.session_state.kill_count = 0
if 'current_word' not in st.session_state: st.session_state.current_word = None
if 'choices' not in st.session_state: st.session_state.choices = []
if 'last_action' not in st.session_state: st.session_state.last_action = None 
if 'session_missed' not in st.session_state: st.session_state.session_missed = []
if 'show_result' not in st.session_state: st.session_state.show_result = False

def fetch_new_word():
    res = conn.table("words").select("*").order("miss_count", desc=True).limit(20).execute()
    if res.data:
        word_data = random.choice(res.data)
        st.session_state.current_word = word_data
        st.session_state.enemy_hp = 100 # 新しい敵のHP
        
        correct_id = word_data['id']
        all_words = conn.table("words").select("id, meaning").limit(40).execute().data
        dummies = [w for w in all_words if w['id'] != correct_id]
        raw_choices = random.sample(dummies, 3) + [{'id': correct_id, 'meaning': word_data['meaning']}]
        random.shuffle(raw_choices)
        st.session_state.choices = raw_choices

# --- UIセクション ---
tab1, tab2 = st.tabs(["⚔️ DUNGEON", "⚙️ SYSTEM"])

with tab1:
    if st.session_state.show_result:
        st.markdown('<div class="status-card">', unsafe_allow_html=True)
        st.title("🏆 RESULT")
        c1, c2 = st.columns(2)
        c1.metric("倒した数", f"{st.session_state.kill_count} 体")
        c2.metric("最大コンボ", f"{st.session_state.max_combo} 回")
        
        if st.session_state.session_missed:
            st.write("### 復習リスト")
            st.table(pd.DataFrame(st.session_state.session_missed).drop_duplicates())
        
        if st.button("もう一度挑戦する"):
            st.session_state.show_result = False
            st.session_state.kill_count = 0
            st.session_state.max_combo = 0
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    elif not st.session_state.game_started:
        st.title("🛡️ WORD DUNGEON")
        if st.button("🔥 探索開始"):
            st.session_state.game_started = True
            st.session_state.player_hp = 100
            st.session_state.kill_count = 0
            st.session_state.combo = 0
            st.session_state.max_combo = 0
            st.session_state.last_action = None
            fetch_new_word()
            st.rerun()

    else:
        st.markdown('<div class="status-card">', unsafe_allow_html=True)
        
        # コンボとダメージ表示
        col_info1, col_info2 = st.columns([1, 1])
        with col_info1:
            if st.session_state.combo > 0:
                st.markdown(f'<div class="combo-text">{st.session_state.combo} COMBO</div>', unsafe_allow_html=True)
        with col_info2:
            if st.session_state.last_action == "hit":
                st.markdown('<div class="dmg-give">CRITICAL: -50 DMG</div>', unsafe_allow_html=True)
            elif st.session_state.last_action == "miss":
                st.markdown(f'<div class="dmg-take">MISS: -25 DMG</div>', unsafe_allow_html=True)
                st.markdown(f'<small>正解: {st.session_state.prev_ans}</small>', unsafe_allow_html=True)

        # HPバー
        hp_p, hp_e = st.columns(2)
        hp_p.write(f"YOU: {st.session_state.player_hp} HP")
        hp_p.progress(max(0, st.session_state.player_hp) / 100)
        hp_e.write(f"ENEMY: {st.session_state.enemy_hp} HP")
        hp_e.progress(max(0, st.session_state.enemy_hp) / 100)
        
        word_data = st.session_state.current_word
        st.markdown(f"<h1 style='font-size:3.5rem; color:#60a5fa;'>{word_data['word']}</h1>", unsafe_allow_html=True)
        
        cols = st.columns(2)
        for i, choice in enumerate(st.session_state.choices):
            with cols[i % 2]:
                if st.button(choice['meaning'], key=f"btn_{i}"):
                    if choice['id'] == word_data['id']:
                        st.session_state.last_action = "hit"
                        st.session_state.enemy_hp -= 50
                        st.session_state.combo += 1
                        st.session_state.max_combo = max(st.session_state.max_combo, st.session_state.combo)
                        
                        if st.session_state.enemy_hp <= 0:
                            st.session_state.kill_count += 1
                            fetch_new_word()
                    else:
                        st.session_state.last_action = "miss"
                        st.session_state.prev_ans = word_data['meaning']
                        st.session_state.player_hp -= 25
                        st.session_state.combo = 0
                        st.session_state.session_missed.append({"英単語": word_data['word'], "意味": word_data['meaning']})
                        fetch_new_word() # ミスしても単語は変える
                    
                    if st.session_state.player_hp <= 0:
                        st.session_state.game_started = False
                        st.session_state.show_result = True
                    st.rerun()
        
        st.divider()
        if st.button("🏃 拠点へ戻る"):
            st.session_state.game_started = False
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

with tab2:
    st.write("単語追加などはここで行ってください")

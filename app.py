import streamlit as st
from st_supabase_connection import SupabaseConnection
import pandas as pd
import random

# 1. ページ設定と豪華なデザイン
st.set_page_config(page_title="Word Dungeon: Legend", page_icon="👑", layout="wide")
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@900&family=Inter:wght@400;700&display=swap');
    
    html, body, [class*="css"] { font-family: 'Inter', 'Noto Sans JP', sans-serif; background-color: #020617; color: #f1f5f9; }
    
    /* ボタンデザイン：高級感のあるグラデーション */
    .stButton>button { 
        width: 100%; border-radius: 16px; height: 65px; font-weight: 700; font-size: 1.1rem;
        background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
        color: white; border: none; transition: 0.3s;
    }
    .stButton>button:hover { transform: scale(1.02); box-shadow: 0 0 20px rgba(168, 85, 247, 0.4); }
    
    /* リザルトカード */
    .result-card { 
        background: linear-gradient(180deg, #1e293b 0%, #0f172a 100%);
        padding: 40px; border-radius: 24px; border: 2px solid #3b82f6;
        text-align: center; margin-bottom: 30px;
    }
    .rank-s { color: #ffb703; font-size: 80px; font-weight: 900; text-shadow: 0 0 20px #fbbf24; }
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

def fetch_new_word():
    res = conn.table("words").select("*").order("miss_count", desc=True).limit(20).execute()
    if res.data:
        word_data = random.choice(res.data)
        st.session_state.current_word = word_data
        st.session_state.enemy_hp = 100
        
        # 選択肢の固定
        correct_id = word_data['id']
        all_words = conn.table("words").select("id, meaning").limit(30).execute().data
        dummies = [w for w in all_words if w['id'] != correct_id]
        raw_choices = random.sample(dummies, 3) + [{'id': correct_id, 'meaning': word_data['meaning']}]
        random.shuffle(raw_choices)
        st.session_state.choices = raw_choices

# --- メイン画面 ---
tab1, tab2 = st.tabs(["⚔️ DUNGEON", "🛠️ ADMIN"])

with tab1:
    # A. 戦績（リザルト）画面
    if st.session_state.show_result:
        st.markdown('<div class="result-card">', unsafe_allow_html=True)
        score = st.session_state.session_score
        rank = "S" if score >= 10 else "A" if score >= 7 else "B" if score >= 4 else "C"
        st.markdown(f'<div class="rank-s">{rank}</div>', unsafe_allow_html=True)
        st.subheader(f"冒険終了！討伐数: {score}")
        
        if st.session_state.session_missed:
            st.write("--- 復習すべき苦手モンスター ---")
            missed_df = pd.DataFrame(st.session_state.session_missed).drop_duplicates()
            st.table(missed_df)
            
        if st.button("拠点を立て直して再出撃"):
            st.session_state.show_result = False
            st.session_state.session_score = 0
            st.session_state.session_missed = []
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # B. スタート画面
    elif not st.session_state.game_started:
        st.title("🛡️ WORD DUNGEON LEGEND")
        col_start, _ = st.columns([1, 2])
        with col_start:
            if st.button("🔥 ダンジョンに潜入"):
                st.session_state.game_started = True
                st.session_state.player_hp = 100
                fetch_new_word()
                st.rerun()

    # C. バトル画面
    else:
        st.markdown(f'<div style="background:#1e293b; padding:20px; border-radius:20px; border-left:10px solid #6366f1;">', unsafe_allow_html=True)
        hp_col1, hp_col2 = st.columns(2)
        hp_col1.metric("PLAYER HP", f"{st.session_state.player_hp}%")
        hp_col2.metric("ENEMY HP", f"{st.session_state.enemy_hp}%")
        
        word_data = st.session_state.current_word
        st.title(f"👾 {word_data['word']}")
        
        cols = st.columns(2)
        for i, choice in enumerate(st.session_state.choices):
            with cols[i % 2]:
                if st.button(choice['meaning'], key=f"c_{i}"):
                    if choice['id'] == word_data['id']:
                        st.success("⭕ クリティカル！")
                        st.session_state.enemy_hp -= 50 # 2撃で討伐
                        if st.session_state.enemy_hp <= 0:
                            st.session_state.session_score += 1
                            conn.table("words").update({"correct_count": word_data['correct_count'] + 1}).eq("id", word_data['id']).execute()
                            fetch_new_word()
                    else:
                        st.error(f"❌ 被弾！ 正解は「{word_data['meaning']}」")
                        st.session_state.player_hp -= 25
                        st.session_state.session_missed.append({"英単語": word_data['word'], "意味": word_data['meaning']})
                        conn.table("words").update({"miss_count": word_data['miss_count'] + 1}).eq("id", word_data['id']).execute()
                    
                    if st.session_state.player_hp <= 0:
                        st.session_state.game_started = False
                        st.session_state.show_result = True
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# --- Tab 2: 単語管理 ---
with tab2:
    st.header("⚙️ データベース管理")
    
    if st.button("📦 サンプル単語リストを一括追加"):
        sample_words = [
            {"word": "Reluctant", "meaning": "気が進まない"},
            {"word": "Meticulous", "meaning": "細心の注意を払った"},
            {"word": "Persistent", "meaning": "粘り強い"},
            {"word": "Vague", "meaning": "曖昧な"},
            {"word": "Submit", "meaning": "提出する"},
            {"word": "Inherent", "meaning": "固有の"}
        ]
        for sw in sample_words:
            conn.table("words").insert(sw).execute()
        st.success("追加完了！")
    
    st.divider()
    with st.form("manual_add", clear_on_submit=True):
        w = st.text_input("英単語")
        m = st.text_input("意味")
        if st.form_submit_button("追加"):
            conn.table("words").insert({"word": w, "meaning": m}).execute()
            st.rerun()

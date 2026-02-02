import streamlit as st
from st_supabase_connection import SupabaseConnection
import pandas as pd
import random

# 1. ページ設定とデザイン
st.set_page_config(page_title="Word Dungeon Pro", page_icon="⚔️", layout="wide")
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #0f172a; color: #f1f5f9; }
    .stButton>button { 
        width: 100%; border-radius: 12px; height: 60px; font-weight: 600;
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
        color: white; border: none; transition: all 0.2s;
    }
    .stButton>button:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3); }
    .status-card { background: #1e293b; padding: 20px; border-radius: 16px; border: 1px solid #334155; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# 2. Supabase接続
SUPABASE_URL = "https://fxzrckbhxqsdslrapmav.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZ4enJja2JoeHFzZHNscmFwbWF2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzAwMzY4MjYsImV4cCI6MjA4NTYxMjgyNn0.9RNZWdD09IeEiM3O4ji6CyXufMoGi3UzqmKjAkr93sc"
conn = st.connection("supabase", type=SupabaseConnection, url=SUPABASE_URL, key=SUPABASE_KEY)

# 3. 状態管理（判定ミスを防ぐために重要）
if 'game_started' not in st.session_state: st.session_state.game_started = False
if 'enemy_hp' not in st.session_state: st.session_state.enemy_hp = 100
if 'player_hp' not in st.session_state: st.session_state.player_hp = 100
if 'current_word' not in st.session_state: st.session_state.current_word = None
if 'choices' not in st.session_state: st.session_state.choices = []
if 'missed_list' not in st.session_state: st.session_state.missed_list = [] # 今回の冒険で間違えた単語

def fetch_new_word():
    """新しい単語と選択肢をセットする。再実行で変わらないようsession_stateに保存"""
    res = conn.table("words").select("*").order("miss_count", desc=True).limit(20).execute()
    if res.data:
        word_data = random.choice(res.data)
        st.session_state.current_word = word_data
        st.session_state.enemy_hp = 100
        
        # 選択肢の作成（ここも固定する）
        correct_id = word_data['id']
        all_words = conn.table("words").select("id, meaning").limit(20).execute().data
        dummies = [w for w in all_words if w['id'] != correct_id]
        raw_choices = random.sample(dummies, 3) + [{'id': correct_id, 'meaning': word_data['meaning']}]
        random.shuffle(raw_choices)
        st.session_state.choices = raw_choices

# --- メインロジック ---
tab1, tab2 = st.tabs(["🎮 ダンジョン攻略", "⚙️ 単語管理"])

with tab1:
    if not st.session_state.game_started:
        st.title("🛡️ WORD DUNGEON PRO")
        
        # 前回の戦績表示
        if st.session_state.missed_list:
            st.error("前回の冒険で間違えた単語リスト:")
            st.write(", ".join(list(set(st.session_state.missed_list))))
            if st.button("戦績をクリアして新しく始める"):
                st.session_state.missed_list = []
                st.rerun()
        else:
            if st.button("🚀 探索を開始する"):
                st.session_state.game_started = True
                st.session_state.player_hp = 100
                st.session_state.missed_list = []
                fetch_new_word()
                st.rerun()
    else:
        # --- バトル画面 ---
        st.markdown('<div class="status-card">', unsafe_allow_html=True)
        col_hp1, col_hp2 = st.columns(2)
        with col_hp1:
            st.write(f"❤️ PLAYER HP: {st.session_state.player_hp}%")
            st.progress(max(0, st.session_state.player_hp) / 100)
        with col_hp2:
            st.write(f"👾 ENEMY HP: {st.session_state.enemy_hp}%")
            st.progress(max(0, st.session_state.enemy_hp) / 100)
        
        word_data = st.session_state.current_word
        st.subheader(f"英単語モンスター: {word_data['word']}")
        
        # ボタンクリック時の判定
        correct_id = word_data['id']
        cols = st.columns(2)
        for i, choice in enumerate(st.session_state.choices):
            with cols[i % 2]:
                if st.button(choice['meaning'], key=f"c_{i}"):
                    if choice['id'] == correct_id:
                        st.toast("⭕ クリティカル！", icon="⚔️")
                        st.session_state.enemy_hp -= 34
                        conn.table("words").update({"correct_count": word_data['correct_count'] + 1}).eq("id", correct_id).execute()
                        if st.session_state.enemy_hp <= 0:
                            fetch_new_word()
                            st.rerun()
                    else:
                        st.toast(f"❌ 痛恨！ 正解は「{word_data['meaning']}」", icon="⚠️")
                        st.session_state.player_hp -= 20
                        st.session_state.missed_list.append(word_data['word']) # 間違えた単語を記録
                        conn.table("words").update({"miss_count": word_data['miss_count'] + 1}).eq("id", correct_id).execute()
                    
                    if st.session_state.player_hp <= 0:
                        st.session_state.game_started = False
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        if st.button("🏃 撤退する"):
            st.session_state.game_started = False
            st.rerun()

with tab2:
    st.header("⚙️ 単語追加")
    with st.form("add_word", clear_on_submit=True):
        w = st.text_input("英単語")
        m = st.text_input("意味")
        if st.form_submit_button("追加"):
            if w and m:
                conn.table("words").insert({"word": w, "meaning": m}).execute()
                st.success("追加しました")

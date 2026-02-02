import streamlit as st
from st_supabase_connection import SupabaseConnection
import pandas as pd
import random

# 1. ページ設定とモダンデザイン
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

# 3. 状態管理
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

# --- タブ切り替え（ゲームと管理画面） ---
tab1, tab2 = st.tabs(["🎮 ダンジョン攻略", "⚙️ 単語管理システム"])

# --- Tab 1: ゲーム画面 ---
with tab1:
    if not st.session_state.game_started:
        st.title("🛡️ WORD DUNGEON PRO")
        st.info("IDベースの精密判定システムへアップグレードされました。")
        if st.button("🚀 探索を開始する"):
            st.session_state.game_started = True
            st.session_state.player_hp = 100
            fetch_new_word()
            st.rerun()
    else:
        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown('<div class="status-card">', unsafe_allow_html=True)
            st.write(f"❤️ PLAYER HP: {st.session_state.player_hp}%")
            st.progress(max(0, st.session_state.player_hp) / 100)
            
            if st.session_state.current_word:
                word_data = st.session_state.current_word
                rank = "[BOSS]" if word_data['miss_count'] >= 5 else "[NORMAL]"
                st.subheader(f"{rank} {word_data['word']}")
                st.write(f"👾 ENEMY HP: {st.session_state.enemy_hp}%")
                st.progress(max(0, st.session_state.enemy_hp) / 100)
                
                if st.session_state.last_result:
                    st.toast(st.session_state.last_result)

                # 判定ロジック：文字列ではなく「ID」を保持させる
                correct_id = word_data['id']
                
                # 選択肢のシャッフル（ダミー単語をDBから取得して混ぜる）
                all_words = conn.table("words").select("id, meaning").limit(20).execute().data
                dummies = [w for w in all_words if w['id'] != correct_id]
                choices = random.sample(dummies, 3) + [{'id': correct_id, 'meaning': word_data['meaning']}]
                random.shuffle(choices)

                cols = st.columns(2)
                for i, choice in enumerate(choices):
                    with cols[i % 2]:
                        # ボタンが押されたとき、その選択肢のIDが正解IDと同じかチェック
                        if st.button(choice['meaning'], key=f"choice_{i}"):
                            if choice['id'] == correct_id:
                                st.session_state.enemy_hp -= 34
                                st.session_state.last_result = "⭕ クリティカル！"
                                conn.table("words").update({"correct_count": word_data['correct_count'] + 1}).eq("id", correct_id).execute()
                                if st.session_state.enemy_hp <= 0:
                                    fetch_new_word()
                            else:
                                st.session_state.player_hp -= 20
                                st.session_state.last_result = f"❌ 痛恨！ 正解は「{word_data['meaning']}」"
                                conn.table("words").update({"miss_count": word_data['miss_count'] + 1}).eq("id", correct_id).execute()
                            
                            if st.session_state.player_hp <= 0:
                                st.session_state.game_started = False
                            st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
            if st.button("🏃 撤退する"):
                st.session_state.game_started = False
                st.rerun()

        with col2:
            st.subheader("📊 討伐データ")
            res_all = conn.table("words").select("word, miss_count").order("miss_count", desc=True).execute()
            st.dataframe(pd.DataFrame(res_all.data), hide_index=True)

# --- Tab 2: 単語管理（追加システム） ---
with tab2:
    st.header("⚙️ 単語管理パネル")
    with st.form("add_word_form", clear_on_submit=True):
        new_word = st.text_input("英単語を入力 (例: Persistent)")
        new_meaning = st.text_input("和訳を入力 (例: しつこい)")
        if st.form_submit_button("➕ 単語をデータベースに追加"):
            if new_word and new_meaning:
                conn.table("words").insert({"word": new_word, "meaning": new_meaning}).execute()
                st.success(f"「{new_word}」を追加しました！")
            else:
                st.warning("両方の項目を入力してください。")
    
    st.divider()
    st.write("現在の登録単語一覧（削除はSupabaseダッシュボードから行えます）")
    all_data = conn.table("words").select("*").execute()
    st.table(pd.DataFrame(all_data.data)[['word', 'meaning', 'miss_count']])

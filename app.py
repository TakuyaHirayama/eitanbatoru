import streamlit as st
from st_supabase_connection import SupabaseConnection
import pandas as pd
import random
import re

# 1. ページ設定とデザイン
st.set_page_config(page_title="Word Dungeon: Legend", page_icon="🏰", layout="wide")
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Press+Start+2P&display=swap');
    html, body, [class*="css"]  {
        font-family: 'Press+Start+2P', cursive;
        background-color: #0d0d0d;
        color: #00ff00;
    }
    .stButton>button { width: 100%; border: 3px solid #00ff00; height: 50px; background-color: #000; color: #00ff00; font-family: 'Press+Start+2P'; font-size: 10px; }
    .stButton>button:hover { background-color: #00ff00; color: #000; }
    .main-box { background-color: #1a1a1a; padding: 20px; border-radius: 10px; border: 4px solid #00ff00; }
    </style>
    """, unsafe_allow_html=True)

# 2. 直接接続
SUPABASE_URL = "https://fxzrckbhxqsdslrapmav.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZ4enJja2JoeHFzZHNscmFwbWF2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzAwMzY4MjYsImV4cCI6MjA4NTYxMjgyNn0.9RNZWdD09IeEiM3O4ji6CyXufMoGi3UzqmKjAkr93sc"
conn = st.connection("supabase", type=SupabaseConnection, url=SUPABASE_URL, key=SUPABASE_KEY)

# 状態管理
if 'game_started' not in st.session_state: st.session_state.game_started = False
if 'enemy_hp' not in st.session_state: st.session_state.enemy_hp = 100
if 'player_hp' not in st.session_state: st.session_state.player_hp = 100
if 'current_word' not in st.session_state: st.session_state.current_word = None
if 'last_result' not in st.session_state: st.session_state.last_result = None

def normalize(text):
    """判定バグを完全に防ぐための正規化関数"""
    if not text: return ""
    # 文字列変換 -> 前後空白削除 -> 改行削除 -> 全角スペース削除 -> 半角スペース削除
    return str(text).strip().replace("\n", "").replace("\r", "").replace("　", "").replace(" ", "")

def fetch_new_word():
    res = conn.table("words").select("*").order("miss_count", desc=True).limit(20).execute()
    if res.data:
        st.session_state.current_word = random.choice(res.data)
        st.session_state.enemy_hp = 100

def reset_all_stats():
    """全単語の統計を初期化"""
    try:
        conn.table("words").update({"correct_count": 0, "miss_count": 0}).neq("word", "").execute()
        st.success("全ての統計をリセットしました！")
    except:
        st.error("リセットに失敗しました。")

# --- スタート画面 ---
if not st.session_state.game_started:
    st.title("🏰 WORD DUNGEON")
    st.markdown('<div style="text-align:center; padding:50px;">', unsafe_allow_html=True)
    if st.button("🔥 ダンジョンに潜入する"):
        st.session_state.game_started = True
        st.session_state.player_hp = 100
        st.session_state.last_result = None
        fetch_new_word()
        st.rerun()
    
    st.write("---")
    if st.button("♻️ 全ての戦績をリセットする"):
        reset_all_stats()
    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# --- 個性の判定ロジック ---
m_count = st.session_state.current_word['miss_count']
if m_count >= 10: rank, color, atk_mul = "[ラスボス]", "#ff0000", 3.0
elif m_count >= 5: rank, color, atk_mul = "[中ボス]", "#ffa500", 1.5
else: rank, color, atk_mul = "[雑魚]", "#00ff00", 1.0

# --- メイン画面 ---
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown(f'<div class="main-box" style="border-color:{color};">', unsafe_allow_html=True)
    # プレイヤーHP
    st.write(f"YOU HP: {st.session_state.player_hp}%")
    st.progress(max(0, st.session_state.player_hp) / 100)
    
    if st.session_state.current_word:
        st.markdown(f'<h2 style="color:{color};">{rank} {st.session_state.current_word["word"]}</h2>', unsafe_allow_html=True)
        st.write(f"ENEMY HP: {st.session_state.enemy_hp}%")
        st.progress(max(0, st.session_state.enemy_hp) / 100)

        if st.session_state.last_result:
            st.info(st.session_state.last_result)

        # 判定用データの正規化
        correct_meaning = st.session_state.current_word['meaning']
        correct_key = normalize(correct_meaning)
        
        # 選択肢生成
        options = [correct_meaning, "本", "車", "猫", "太陽", "月", "空"]
        random_options = random.sample([o for o in options if normalize(o) != correct_key], 3)
        final_options = [correct_meaning] + random_options
        random.shuffle(final_options)

        cols = st.columns(2)
        for i, opt in enumerate(final_options):
            with cols[i % 2]:
                if st.button(opt, key=f"btn_{i}"):
                    if normalize(opt) == correct_key:
                        st.session_state.enemy_hp -= 34
                        st.session_state.last_result = f"⭕ 命中！ {st.session_state.current_word['word']} = {correct_meaning}"
                        conn.table("words").update({"correct_count": st.session_state.current_word['correct_count'] + 1}).eq("id", st.session_state.current_word['id']).execute()
                        if st.session_state.enemy_hp <= 0:
                            st.balloons()
                            fetch_new_word()
                    else:
                        damage = int(15 * atk_mul)
                        st.session_state.player_hp -= damage
                        st.session_state.last_result = f"❌ 被弾！ {damage}ダメージ！ (正解: {correct_meaning})"
                        conn.table("words").update({"miss_count": st.session_state.current_word['miss_count'] + 1}).eq("id", st.session_state.current_word['id']).execute()
                    
                    if st.session_state.player_hp <= 0:
                        st.session_state.game_started = False
                    st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    
    if st.button("🏃 拠点へ帰還する"):
        st.session_state.game_started = False
        st.rerun()

with col2:
    st.subheader("📜 討伐記録")
    res_all = conn.table("words").select("*").execute()
    if res_all.data:
        df = pd.DataFrame(res_all.data)
        df['正答率'] = df.apply(lambda x: f"{(x['correct_count']/(x['correct_count']+x['miss_count'])*100):.0f}%" if (x['correct_count']+x['miss_count']) > 0 else "0%", axis=1)
        st.dataframe(df[['word', 'miss_count', '正答率']].sort_values('miss_count', ascending=False), hide_index=True)

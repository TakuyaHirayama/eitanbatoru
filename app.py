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
        background-color: #0d0d0d;
        color: #00ff00;
    }
    .stButton>button { width: 100%; border: 3px solid #00ff00; height: 60px; background-color: #000; color: #00ff00; }
    .stButton>button:hover { background-color: #00ff00; color: #000; }
    .main-box { background-color: #1a1a1a; padding: 20px; border-radius: 10px; border: 2px solid #00ff00; }
    </style>
    """, unsafe_allow_html=True)

# 2. 直接接続
SUPABASE_URL = "https://fxzrckbhxqsdslrapmav.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZ4enJja2JoeHFzZHNscmFwbWF2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzAwMzY4MjYsImV4cCI6MjA4NTYxMjgyNn0.9RNZWdD09IeEiM3O4ji6CyXufMoGi3UzqmKjAkr93sc"
conn = st.connection("supabase", type=SupabaseConnection, url=SUPABASE_URL, key=SUPABASE_KEY)

# 状態管理の初期化
if 'game_started' not in st.session_state: st.session_state.game_started = False
if 'enemy_hp' not in st.session_state: st.session_state.enemy_hp = 100
if 'player_hp' not in st.session_state: st.session_state.player_hp = 100
if 'current_word' not in st.session_state: st.session_state.current_word = None
if 'last_result' not in st.session_state: st.session_state.last_result = None

def fetch_new_word():
    res = conn.table("words").select("*").order("miss_count", desc=True).limit(10).execute()
    if res.data:
        st.session_state.current_word = random.choice(res.data)

# --- スタート画面 ---
if not st.session_state.game_started:
    st.title("🏰 WORD DUNGEON")
    st.markdown('<div style="text-align:center; padding:100px;">', unsafe_allow_html=True)
    st.subheader("苦手な単語がモンスターとなって現れる...")
    if st.button("🔥 ダンジョンに挑む！"):
        st.session_state.game_started = True
        st.session_state.player_hp = 100
        st.session_state.enemy_hp = 100
        fetch_new_word()
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# --- メインゲーム画面 ---
st.title("⚔️ BATTLE FIELD")

col1, col2 = st.columns([2, 1])

with col1:
    st.markdown('<div class="main-box">', unsafe_allow_html=True)
    
    # プレイヤーHP
    st.write(f"YOU (PLAYER) HP: {st.session_state.player_hp}%")
    st.progress(max(0, st.session_state.player_hp) / 100)
    
    st.divider()

    if st.session_state.current_word:
        st.header(f"MONSTER: {st.session_state.current_word['word']}")
        st.write(f"ENEMY HP: {st.session_state.enemy_hp}%")
        st.progress(max(0, st.session_state.enemy_hp) / 100)

        if st.session_state.last_result:
            st.info(st.session_state.last_result)

        options = [st.session_state.current_word['meaning'], "本", "車", "猫", "太陽"]
        random.shuffle(options)

        cols = st.columns(2)
        for i, opt in enumerate(options):
            with cols[i % 2]:
                if st.button(opt, key=f"btn_{i}"):
                    # 判定バグ対策: strip()で余計な空白を消して比較
                    correct_ans = str(st.session_state.current_word['meaning']).strip()
                    user_ans = str(opt).strip()

                    if user_ans == correct_ans:
                        st.session_state.enemy_hp -= 25
                        st.session_state.last_result = f"⭕ ナイス攻撃！ {st.session_state.current_word['word']} = {correct_ans}"
                        conn.table("words").update({"correct_count": st.session_state.current_word['correct_count'] + 1}).eq("id", st.session_state.current_word['id']).execute()
                    else:
                        # ダメージ計算：基本10 + (その単語の過去ミス回数 * 5)
                        damage = 10 + (st.session_state.current_word['miss_count'] * 5)
                        st.session_state.player_hp -= damage
                        st.session_state.last_result = f"❌ 痛恨のミス！ {damage}ダメージを受けた！ (正解: {correct_ans})"
                        conn.table("words").update({"miss_count": st.session_state.current_word['miss_count'] + 1}).eq("id", st.session_state.current_word['id']).execute()
                    
                    # 決着判定
                    if st.session_state.enemy_hp <= 0:
                        st.balloons()
                        st.success("敵を倒した！")
                        st.session_state.game_started = False # スタートに戻る
                    elif st.session_state.player_hp <= 0:
                        st.error("GAME OVER... あなたは力尽きた。")
                        st.session_state.game_started = False # スタートに戻る
                    
                    fetch_new_word()
                    st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.subheader("📊 討伐記録")
    res_all = conn.table("words").select("*").execute()
    if res_all.data:
        df = pd.DataFrame(res_all.data)
        df['正答率'] = df.apply(lambda x: f"{(x['correct_count']/(x['correct_count']+x['miss_count'])*100):.0f}%" if (x['correct_count']+x['miss_count']) > 0 else "0%", axis=1)
        st.dataframe(df[['word', 'miss_count', '正答率']].sort_values('miss_count', ascending=False), hide_index=True)

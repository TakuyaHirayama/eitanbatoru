import streamlit as st
from st_supabase_connection import SupabaseConnection
import random

# 1. ページ設定とGoogle Fontsの適用 (外部API)
st.set_page_config(page_title="Focus Enemy", page_icon="⚔️")
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Press+Start+2P&display=swap');
    html, body, [class*="css"]  {
        font-family: 'Press+Start+2P', cursive;
    }
    .stButton>button { width: 100%; border: 3px solid #e94560; }
    </style>
    """, unsafe_allow_html=True)

# 2. Supabase接続 (Secrets管理)
conn = st.connection("supabase", type=SupabaseConnection)

# 3. 状態管理の初期化
if 'enemy_hp' not in st.session_state:
    st.session_state.enemy_hp = 100
if 'current_word' not in st.session_state:
    st.session_state.current_word = None

def fetch_new_word():
    # 独自性：miss_countが多い単語を優先して10件取得し、その中からランダム
    res = conn.table("words").select("*").order("miss_count", desc=True).limit(10).execute()
    if res.data:
        st.session_state.current_word = random.choice(res.data)

if st.session_state.current_word is None:
    fetch_new_word()

# --- UIセクション ---
st.title("⚔️ FOCUS ENEMY")
st.subheader(f"TARGET: {st.session_state.current_word['word']}")

# HPゲージ
st.progress(st.session_state.enemy_hp / 100)
st.write(f"ENEMY HP: {st.session_state.enemy_hp}%")

# 回答選択肢（正解 + 適当な3つ）
options = [st.session_state.current_word['meaning'], "本", "車", "猫", "太陽"]
random.shuffle(options)

cols = st.columns(2)
for i, opt in enumerate(options):
    with cols[i % 2]:
        if st.button(opt):
            if opt == st.session_state.current_word['meaning']:
                st.success("HIT!")
                st.session_state.enemy_hp -= 25
                # 正解数を更新
                conn.table("words").update({"correct_count": st.session_state.current_word['correct_count'] + 1}).eq("id", st.session_state.current_word['id']).execute()
            else:
                st.error("MISS! 出現率アップ！")
                # 苦手回数を更新
                conn.table("words").update({"miss_count": st.session_state.current_word['miss_count'] + 1}).eq("id", st.session_state.current_word['id']).execute()
            
            if st.session_state.enemy_hp <= 0:
                st.balloons()
                st.session_state.enemy_hp = 100
            
            fetch_new_word()
            st.rerun()

import streamlit as st
from st_supabase_connection import SupabaseConnection
import pandas as pd
import random
import time

# 1. ページ設定と豪華デザイン
st.set_page_config(page_title="Word Dungeon: Absolute", page_icon="👑", layout="wide")
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700;900&family=Noto+Sans+JP:wght@900&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', 'Noto Sans JP', sans-serif; background-color: #020617; color: #f1f5f9; }
    
    .stButton>button { 
        width: 100%; border-radius: 16px; height: 75px; font-weight: 800; font-size: 1.2rem;
        background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%);
        color: white; border: 1px solid #60a5fa; transition: 0.15s;
    }
    .stButton>button:hover { transform: scale(1.02); box-shadow: 0 0 25px rgba(59, 130, 246, 0.4); }
    
    .status-card { background: #1e293b; padding: 30px; border-radius: 24px; border: 2px solid #334155; text-align: center; }
    .boss-card { background: linear-gradient(180deg, #450a0a 0%, #020617 100%); border: 3px solid #ef4444; }
    
    .combo-text { font-family: 'Orbitron'; color: #fbbf24; font-size: 2.5rem; font-weight: 900; text-shadow: 2px 2px 2px #000; }
    .boss-name { font-family: 'Orbitron'; color: #ef4444; font-size: 4.5rem; text-shadow: 0 0 15px #7f1d1d; }
    .result-rank { font-size: 140px; font-weight: 900; color: #fbbf24; text-shadow: 0 0 30px rgba(251, 191, 36, 0.5); }
    .ans-box { background: #ef4444; color: white; padding: 10px; border-radius: 10px; margin-top: 10px; font-weight: 700; }
    </style>
    """, unsafe_allow_html=True)

# 2. Supabase接続
SUPABASE_URL = "https://fxzrckbhxqsdslrapmav.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZ4enJja2JoeHFzZHNscmFwbWF2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzAwMzY4MjYsImV4cCI6MjA4NTYxMjgyNn0.9RNZWdD09IeEiM3O4ji6CyXufMoGi3UzqmKjAkr93sc"
conn = st.connection("supabase", type=SupabaseConnection, url=SUPABASE_URL, key=SUPABASE_KEY)

# 3. 状態管理
states = {
    'game_started': False, 'player_hp': 100, 'enemy_hp': 100, 'kill_count': 0,
    'combo': 0, 'max_combo': 0, 'start_time': 0, 'current_word': None,
    'choices': [], 'last_action': None, 'session_missed': [], 'show_result': False, 'prev_ans': ""
}
for key, val in states.items():
    if key not in st.session_state: st.session_state[key] = val

def fetch_new_word():
    # ラスボス(10体目)はミスが多い苦手単語を優先
    res = conn.table("words").select("*").order("miss_count", desc=True).limit(30).execute()
    if res.data:
        word_data = res.data[0] if st.session_state.kill_count == 9 else random.choice(res.data)
        st.session_state.current_word = word_data
        st.session_state.enemy_hp = 200 if st.session_state.kill_count == 9 else 100
        
        correct_id = word_data['id']
        all_words = conn.table("words").select("id, meaning").limit(60).execute().data
        dummies = random.sample([w for w in all_words if w['id'] != correct_id], 3)
        raw_choices = dummies + [{'id': correct_id, 'meaning': word_data['meaning']}]
        random.shuffle(raw_choices)
        st.session_state.choices = raw_choices

# --- メイン画面 ---
tab1, tab2 = st.tabs(["⚔️ DUNGEON", "⚙️ SYSTEM"])

with tab1:
    if st.session_state.show_result:
        st.markdown('<div class="status-card">', unsafe_allow_html=True)
        clear_time = int(time.time() - st.session_state.start_time)
        rank = "S" if st.session_state.kill_count >= 10 and clear_time < 50 else "A" if st.session_state.kill_count >= 10 else "B"
        st.markdown(f'<div class="result-rank">{rank}</div>', unsafe_allow_html=True)
        st.title("VICTORY" if st.session_state.kill_count >= 10 else "DEFEAT")
        
        c1, c2, c3 = st.columns(3)
        c1.metric("討伐数", f"{st.session_state.kill_count}/10")
        c2.metric("最大コンボ", f"{st.session_state.max_combo}")
        c3.metric("攻略タイム", f"{clear_time}秒")
        
        if st.session_state.session_missed:
            st.write("--- 敗北の原因となった単語 ---")
            st.table(pd.DataFrame(st.session_state.session_missed).drop_duplicates())
        
        if st.button("リベンジを開始する"):
            st.session_state.show_result = False
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    elif not st.session_state.game_started:
        st.title("🛡️ WORD DUNGEON")
        st.write("目指せ10体討伐。最深部には最強のラスボスが待つ。")
        if st.button("🔥 ダンジョンに潜入する"):
            st.session_state.update({'game_started': True, 'player_hp': 100, 'kill_count': 0, 'combo': 0, 'max_combo': 0, 'session_missed': [], 'start_time': time.time(), 'last_action': None})
            fetch_new_word()
            st.rerun()

    else:
        is_boss = st.session_state.kill_count == 9
        st.markdown(f'<div class="{"status-card boss-card" if is_boss else "status-card"}">', unsafe_allow_html=True)
        
        # ヘッダー情報
        col_h1, col_h2, col_h3 = st.columns([1,2,1])
        col_h1.metric("YOUR HP", f"{st.session_state.player_hp}%")
        col_h3.metric("STAGE", f"{st.session_state.kill_count + 1}/10")
        with col_h2:
            if st.session_state.combo > 1: st.markdown(f'<div class="combo-text">{st.session_state.combo} COMBO</div>', unsafe_allow_html=True)
            st.write(f"ENEMY HP: {st.session_state.enemy_hp}%")
            st.progress(max(0, st.session_state.enemy_hp) / (200 if is_boss else 100))

        # 単語とフィードバック
        word_data = st.session_state.current_word
        st.markdown(f'<h1 class="{"boss-name" if is_boss else ""}" style="font-size:3.5rem;">{word_data["word"]}</h1>', unsafe_allow_html=True)
        
        if st.session_state.last_action == "miss":
            st.markdown(f'<div class="ans-box">正解: {st.session_state.prev_ans}</div>', unsafe_allow_html=True)

        # ボタン
        cols = st.columns(2)
        for i, choice in enumerate(st.session_state.choices):
            with cols[i % 2]:
                if st.button(choice['meaning'], key=f"btn_{i}"):
                    if choice['id'] == word_data['id']:
                        st.session_state.enemy_hp -= 50
                        st.session_state.combo += 1
                        st.session_state.max_combo = max(st.session_state.max_combo, st.session_state.combo)
                        st.session_state.last_action = "hit"
                        if st.session_state.enemy_hp <= 0:
                            st.session_state.kill_count += 1
                            if st.session_state.kill_count >= 10:
                                st.session_state.show_result = True
                                st.session_state.game_started = False
                            else: fetch_new_word()
                    else:
                        st.session_state.player_hp -= (40 if is_boss else 20)
                        st.session_state.prev_ans = word_data['meaning']
                        st.session_state.combo = 0
                        st.session_state.last_action = "miss"
                        st.session_state.session_missed.append({"英単語": word_data['word'], "意味": word_data['meaning']})
                        fetch_new_word()

                    if st.session_state.player_hp <= 0:
                        st.session_state.show_result = True
                        st.session_state.game_started = False
                    st.rerun()

        st.divider()
        if st.button("🏃 拠点へ戻る"):
            st.session_state.game_started = False
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

with tab2:
    st.header("⚙️ システム管理")
    with st.form("admin_add", clear_on_submit=True):
        aw = st.text_input("英単語")
        am = st.text_input("意味")
        if st.form_submit_button("DBに追加"):
            if aw and am:
                conn.table("words").insert({"word": aw, "meaning": am}).execute()
                st.success(f"{aw} を追加しました")
            else: st.error("入力を確認してください")

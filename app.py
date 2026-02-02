import streamlit as st
from st_supabase_connection import SupabaseConnection
import pandas as pd
import random

# 1. ページ設定とデザイン
st.set_page_config(page_title="Word Dungeon: Speed", page_icon="⚡", layout="wide")
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@900&family=Inter:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', 'Noto Sans JP', sans-serif; background-color: #020617; color: #f1f5f9; }
    .stButton>button { 
        width: 100%; border-radius: 16px; height: 65px; font-weight: 700; font-size: 1.1rem;
        background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
        color: white; border: none; transition: 0.3s;
    }
    .stButton>button:hover { transform: scale(1.02); box-shadow: 0 0 20px rgba(168, 85, 247, 0.4); }
    .result-card { 
        background: linear-gradient(180deg, #1e293b 0%, #0f172a 100%);
        padding: 40px; border-radius: 24px; border: 2px solid #3b82f6;
        text-align: center; margin-bottom: 30px;
    }
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
    """新しい単語と選択肢を完全にリフレッシュして保存する"""
    res = conn.table("words").select("*").order("miss_count", desc=True).limit(25).execute()
    if res.data:
        word_data = random.choice(res.data)
        st.session_state.current_word = word_data
        
        # 選択肢の固定（IDベース）
        correct_id = word_data['id']
        all_words_res = conn.table("words").select("id, meaning").limit(50).execute()
        all_words = all_words_res.data
        
        # 正解以外のダミーを3つ選ぶ
        dummies = [w for w in all_words if w['id'] != correct_id]
        raw_choices = random.sample(dummies, 3) + [{'id': correct_id, 'meaning': word_data['meaning']}]
        random.shuffle(raw_choices)
        st.session_state.choices = raw_choices

# --- メインロジック ---
tab1, tab2 = st.tabs(["⚔️ DUNGEON", "🛠️ ADMIN"])

with tab1:
    if st.session_state.show_result:
        # 豪華な戦績画面
        st.markdown('<div class="result-card">', unsafe_allow_html=True)
        score = st.session_state.session_score
        rank = "S" if score >= 15 else "A" if score >= 10 else "B" if score >= 5 else "C"
        st.markdown(f'<div style="font-size:80px; font-weight:900; color:#fbbf24;">{rank}</div>', unsafe_allow_html=True)
        st.subheader(f"今回の討伐数: {score}")
        if st.session_state.session_missed:
            st.write("復習が必要な単語:")
            st.table(pd.DataFrame(st.session_state.session_missed).drop_duplicates())
        if st.button("もう一度挑戦"):
            st.session_state.show_result = False
            st.session_state.session_score = 0
            st.session_state.session_missed = []
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    elif not st.session_state.game_started:
        st.title("🛡️ WORD DUNGEON")
        if st.button("🔥 探索を開始する"):
            st.session_state.game_started = True
            st.session_state.player_hp = 100
            st.session_state.enemy_hp = 100
            fetch_new_word()
            st.rerun()

    else:
        # バトル画面
        st.markdown(f'<div style="background:#1e293b; padding:20px; border-radius:20px;">', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        c1.metric("PLAYER HP", f"{st.session_state.player_hp}%")
        c2.metric("ENEMY TOTAL HP", f"{st.session_state.enemy_hp}%")
        
        word_data = st.session_state.current_word
        st.title(f"👾 {word_data['word']}")
        
        cols = st.columns(2)
        for i, choice in enumerate(st.session_state.choices):
            with cols[i % 2]:
                if st.button(choice['meaning'], key=f"btn_{i}"):
                    # 1. 正誤判定
                    if choice['id'] == word_data['id']:
                        st.toast(f"⭕ 正解: {word_data['word']} = {word_data['meaning']}")
                        st.session_state.session_score += 1
                        st.session_state.enemy_hp -= 10 # 敵全体のHPを減らす演出
                        # Supabase更新
                        conn.table("words").update({"correct_count": word_data['correct_count'] + 1}).eq("id", word_data['id']).execute()
                    else:
                        st.toast(f"❌ 不正解: {word_data['word']} は「{word_data['meaning']}」")
                        st.session_state.player_hp -= 20
                        st.session_state.session_missed.append({"英単語": word_data['word'], "和訳": word_data['meaning']})
                        # Supabase更新
                        conn.table("words").update({"miss_count": word_data['miss_count'] + 1}).eq("id", word_data['id']).execute()

                    # 2. 状態チェック
                    if st.session_state.player_hp <= 0 or st.session_state.enemy_hp <= 0:
                        st.session_state.game_started = False
                        st.session_state.show_result = True
                    else:
                        # 3. 【重要】判定が終わったら即座に次の単語へ！
                        fetch_new_word()
                    
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

with tab2:
    st.header("⚙️ 管理パネル")
    if st.button("📦 サンプル単語を投入"):
        samples = [
            {"word": "Reluctant", "meaning": "気が進まない"},
            {"word": "Meticulous", "meaning": "細心の注意を払った"},
            {"word": "Vague", "meaning": "曖昧な"}
        ]
        for s in samples: conn.table("words").insert(s).execute()
        st.success("投入完了")

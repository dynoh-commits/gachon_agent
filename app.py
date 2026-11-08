from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")
st.set_page_config(page_title="OO 학원 평가 도우미", page_icon="📘", layout="wide")

# 페이지 객체 생성
home = st.Page("page_1.py", title="홈", icon="🏠", default=True)
analysis = st.Page("page_2.py", title="성적 분석", icon="📊")

# 네비게이션 설정
navigation = st.navigation([home, analysis], position="top")

# 실행
navigation.run()
import streamlit as st
import pandas as pd

# 페이지 객체 생성
page_1 = st.Page("page_1.py", title="Page 1", icon="1⃣")
page_2 = st.Page("page_2.py", title="Page 2", icon="2⃣")

# 네비게이션 설정
pages = st.navigation([page_1, page_2], position='top')

# 실행
pages.run()
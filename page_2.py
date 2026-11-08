import streamlit as st
import pandas as pd

# 파일 업로더 생성
uploaded_files = st.file_uploader(
    "데이터 업로드\nDrag & Drop",
    type=['xlsx', 'xls', 'pdf'],
    accept_multiple_files=True,
    key='my_uploader',       
    )

# 파일 리스트가 비어있지 않은지 확인
if uploaded_files:
    for uploaded_file in uploaded_files:
        try:
            df = pd.read_excel(uploaded_file)
        
            # 화면에 출력
            st.write(f"### 파일명: {uploaded_file.name}")
            st.dataframe(df)
            st.divider() # 구분선 추가
        
        except Exception as e:
            st.error(f"파일을 읽는 중 오류 발생: {e}")
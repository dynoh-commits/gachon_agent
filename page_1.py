import base64
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components


st.markdown("<div style='height:3vh'></div>", unsafe_allow_html=True)
logo = Path(__file__).parent / "assets" / "marklogo-kor_eng-vertical.jpg"
logo_b64 = base64.b64encode(logo.read_bytes()).decode("ascii")
components.html(
    f"""<!doctype html>
    <html><head><style>
    html, body {{ margin:0; padding:0; width:100%; }}
    .logo-wrap {{ width:100%; height:210px; display:flex; justify-content:center; align-items:center; }}
    .logo-wrap img {{ display:block; width:180px; height:auto; }}
    </style></head><body>
    <div class="logo-wrap"><img src="data:image/jpeg;base64,{logo_b64}" alt="가천대학교 로고"></div>
    </body></html>""",
    height=210,
    scrolling=False,
)

st.markdown(
    "<h1 style='text-align:center; margin:0.2rem 0 0.8rem;'>OO 학원 평가 도우미</h1>",
    unsafe_allow_html=True,
)
st.markdown(
    "<p style='text-align:center; color:#5B6B73; font-size:1.1rem;'>영어 시험 채점과 성적 분석을 간편하게</p>",
    unsafe_allow_html=True,
)

st.markdown("<div style='height:2vh'></div>", unsafe_allow_html=True)
a, b, c = st.columns(3)
a.metric("자동 채점", "문항별 배점 반영")
b.metric("Excel 결과", "반 통계 · 학생별 정오")
c.metric("결과 상담", "성적 질문 · 유사문항")

st.markdown("<div style='height:2vh'></div>", unsafe_allow_html=True)
_, button_col, _ = st.columns([1, 1, 1])
with button_col:
    if st.button("성적 분석 시작하기 →", type="primary", use_container_width=True):
        st.switch_page("page_2.py")

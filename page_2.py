import streamlit as st

from exam_agent.chat import answer_turn
from exam_agent.grading import grade_exam, make_workbook
from exam_agent.parsers import parse_answer_key, parse_exam_questions, read_responses


if "messages" not in st.session_state:
    st.session_state.messages = []
if "results" not in st.session_state:
    st.session_state.results = None
if "workbook" not in st.session_state:
    st.session_state.workbook = None
if "questions" not in st.session_state:
    st.session_state.questions = {}


with st.sidebar:
    st.header("시험 자료 업로드")
    question_pdf = st.file_uploader("영어 문제 PDF", type=["pdf"], key="question_pdf")
    response_file = st.file_uploader("학생 OMR 응답 데이터", type=["xlsx", "xls", "csv"], key="response_file")
    key_pdf = st.file_uploader("정답·배점 PDF", type=["pdf"], key="key_pdf")
    if st.button("채점 및 분석 시작", type="primary", use_container_width=True):
        if not all((question_pdf, response_file, key_pdf)):
            st.error("문제 PDF, 학생 응답 파일, 정답 PDF를 모두 올려주세요.")
        else:
            with st.spinner("문항과 정답표를 읽고 채점하고 있습니다..."):
                try:
                    key = parse_answer_key(key_pdf.getvalue())
                    responses = read_responses(response_file.getvalue(), response_file.name)
                    questions = parse_exam_questions(question_pdf.getvalue())
                    results = grade_exam(responses, key)
                    st.session_state.results = results
                    st.session_state.questions = questions
                    st.session_state.workbook = make_workbook(results)
                    st.session_state.messages = []
                    st.success(f"{len(results['students'])}명, {len(key)}문항 채점을 완료했습니다.")
                except Exception as exc:
                    st.session_state.results = None
                    st.session_state.workbook = None
                    st.error(f"파일을 처리하지 못했습니다: {exc}")
    if st.session_state.workbook is not None:
        st.download_button(
            "Excel 결과 다운로드",
            data=st.session_state.workbook,
            file_name="영어시험_채점결과.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )


st.title("시험 성적 분석")
results = st.session_state.results
if results is None:
    st.info("왼쪽에서 문제 PDF, 학생 응답 파일, 정답·배점 PDF를 올리고 채점을 시작하세요.")
else:
    summary = results["summary"]
    cols = st.columns(4)
    cols[0].metric("응시 학생", f"{summary['student_count']}명")
    cols[1].metric("평균", f"{summary['mean']:.1f}점")
    cols[2].metric("중앙값", f"{summary['median']:.1f}점")
    cols[3].metric("표준편차", f"{summary['std']:.1f}점")

    st.subheader("문항별 결과")
    st.dataframe(results["question_stats"], use_container_width=True, hide_index=True)
    st.subheader("학생별 점수와 문항별 정오")
    st.dataframe(results["student_table"], use_container_width=True, hide_index=True)
    st.divider()
    st.subheader("성적 분석 상담")
    st.caption("채점 결과, 학생별 점수, 가장 많이 틀린 유형의 유사문항을 물어보세요.")
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    prompt = st.chat_input("예: 평균 점수는? / 가장 많이 틀린 유형의 문제를 만들어줘")
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.chat_message("assistant"):
            with st.spinner("답변을 준비하고 있어요..."):
                reply = answer_turn(
                    prompt,
                    st.session_state.messages[:-1],
                    results,
                    st.session_state.questions,
                )
            st.markdown(reply)
        st.session_state.messages.append({"role": "assistant", "content": reply})

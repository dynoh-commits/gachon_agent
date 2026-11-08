from __future__ import annotations

import io

import pandas as pd
from openpyxl.styles import Font
from openpyxl.utils import get_column_letter


def grade_exam(responses: pd.DataFrame, answer_key: dict[int, dict[str, int]]) -> dict:
    question_numbers = sorted(answer_key)
    missing = [q for q in question_numbers if q not in responses.columns]
    if missing:
        raise ValueError(f"응답 파일에 문항이 없습니다: {', '.join(map(str, missing))}")
    if responses["학생명"].isna().any() or (responses["학생명"].str.len() == 0).any():
        raise ValueError("학생 이름이 비어 있는 행이 있습니다.")

    correctness = pd.DataFrame(index=responses.index)
    scores = []
    for q in question_numbers:
        answer = answer_key[q]["answer"]
        points = answer_key[q]["points"]
        correctness[q] = responses[q].eq(answer)
        scores.append(correctness[q].astype(int) * points)
    score_series = pd.concat(scores, axis=1).sum(axis=1)
    total_points = sum(item["points"] for item in answer_key.values())

    student_table = pd.DataFrame({"학생명": responses["학생명"], "점수": score_series, "만점": total_points})
    for q in question_numbers:
        student_table[f"Q{q:02d}_정오"] = correctness[q].map({True: "정답", False: "오답"})
    student_table = student_table.sort_values(["점수", "학생명"], ascending=[False, True]).reset_index(drop=True)

    question_stats = pd.DataFrame([
        {
            "문항": q,
            "정답": answer_key[q]["answer"],
            "배점": answer_key[q]["points"],
            "정답 수": int(correctness[q].sum()),
            "오답 수": int(len(correctness) - correctness[q].sum()),
            "정답률(%)": round(float(correctness[q].mean() * 100), 1),
        }
        for q in question_numbers
    ]).sort_values(["오답 수", "문항"], ascending=[False, True]).reset_index(drop=True)

    score_values = student_table["점수"]
    summary = {
        "student_count": len(student_table),
        "mean": float(score_values.mean()),
        "median": float(score_values.median()),
        "std": float(score_values.std(ddof=0)),
        "min": int(score_values.min()),
        "max": int(score_values.max()),
        "total_points": total_points,
        "most_missed": question_stats.head(3)["문항"].astype(int).tolist(),
    }
    detail = responses.rename(columns={q: f"Q{q:02d}_응답" for q in question_numbers}).copy()
    detail.insert(1, "점수", score_series)
    return {
        "summary": summary,
        "students": student_table["학생명"].tolist(),
        "student_table": student_table,
        "question_stats": question_stats,
        "answers": answer_key,
        "responses": detail,
        "correctness": correctness,
    }


def make_workbook(results: dict) -> bytes:
    output = io.BytesIO()
    summary = results["summary"]
    summary_frame = pd.DataFrame([
        ("응시 학생 수", summary["student_count"]),
        ("평균", round(summary["mean"], 2)),
        ("중앙값", summary["median"]),
        ("표준편차", round(summary["std"], 2)),
        ("최고점", summary["max"]),
        ("최저점", summary["min"]),
        ("만점", summary["total_points"]),
        ("오답이 많은 문항 1", summary["most_missed"][0] if summary["most_missed"] else ""),
        ("오답이 많은 문항 2", summary["most_missed"][1] if len(summary["most_missed"]) > 1 else ""),
        ("오답이 많은 문항 3", summary["most_missed"][2] if len(summary["most_missed"]) > 2 else ""),
    ], columns=["항목", "값"])
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        summary_frame.to_excel(writer, sheet_name="반 통계", index=False)
        summary_ws = writer.sheets["반 통계"]
        student_title_row = len(summary_frame) + 3
        summary_ws.cell(row=student_title_row, column=1, value="학생별 점수와 문항별 정오")
        summary_ws.cell(row=student_title_row, column=1).font = Font(bold=True, size=12)
        student_startrow = student_title_row
        results["student_table"].to_excel(
            writer,
            sheet_name="반 통계",
            index=False,
            startrow=student_startrow,
        )
        last_student_row = student_startrow + len(results["student_table"]) + 1
        last_student_col = get_column_letter(len(results["student_table"].columns))
        summary_ws.auto_filter.ref = f"A{student_startrow + 1}:{last_student_col}{last_student_row}"
        results["student_table"].to_excel(writer, sheet_name="학생별 결과", index=False)
        results["question_stats"].sort_values("문항").to_excel(writer, sheet_name="문항별 통계", index=False)
        results["responses"].to_excel(writer, sheet_name="응답 원본", index=False)
        for worksheet in writer.book.worksheets:
            worksheet.freeze_panes = "B2"
            if worksheet.title != "반 통계":
                worksheet.auto_filter.ref = worksheet.dimensions
            for column in worksheet.columns:
                width = min(max(max(len(str(cell.value or "")) for cell in column) + 2, 10), 28)
                worksheet.column_dimensions[column[0].column_letter].width = width
    return output.getvalue()

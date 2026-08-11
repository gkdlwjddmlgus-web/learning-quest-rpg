from game_core import *


def render_wrong_tab() -> None:
    st.subheader("망각의 도서관")
    wrongs = st.session_state.extra["wrong_questions"]
    st.write(f"저장된 오답: **{len(wrongs)}개** · 기억의 조각: **{st.session_state.extra['memory_shards']}개**")

    if not wrongs:
        st.info("오답이 없습니다.")
    else:
        for idx, wrong in enumerate(wrongs[:10]):
            with st.expander(f"{wrong['category']} · {wrong['question'][:55]}"):
                st.write(wrong["question"])
                qtype = get_effective_question_type(wrong)
                options = wrong.get("options") or []

                selected = None
                answer_text = ""
                if qtype == "multiple_choice" and options:
                    selected = st.radio("다시 풀기", options, index=None, key=f"wrong_mc_{idx}")
                else:
                    expected = parse_short_answers(wrong.get("answer", ""))
                    multi_slot = is_multi_slot_short_answer(
                        wrong.get("question", ""),
                        expected,
                    )

                    placeholder = get_short_answer_placeholder(
                        wrong.get("question", ""),
                        expected,
                    )

                    answer_text = st.text_input(
                        "다시 풀기",
                        placeholder=placeholder,
                        key=f"wrong_short_{idx}",
                    )

                    if multi_slot:
                        st.caption("여러 빈칸 문제입니다. 정답을 순서대로 입력하세요. 쉼표, / 또는 줄바꿈으로 구분할 수 있습니다.")
                    elif len(expected) > 1:
                        st.caption("허용되는 정답 표현 중 하나만 입력하면 됩니다.")

                if st.button("복습 제출", key=f"wrong_submit_{idx}"):
                    if qtype == "multiple_choice" and options:
                        is_correct = selected == wrong.get("answer")
                    else:
                        is_correct, _ = evaluate_short_answer(
                            answer_text,
                            wrong.get("answer", ""),
                            wrong.get("question", ""),
                        )

                    review_answer = selected if (qtype == "multiple_choice" and options) else answer_text
                    log_question_attempt(
                        wrong,
                        review_answer,
                        is_correct,
                        xp_earned=15 if is_correct else 0,
                        attempt_type="review",
                    )

                    if is_correct:
                        st.session_state.extra["memory_shards"] += 1
                        st.session_state.xp += 15
                        st.session_state.extra["wrong_questions"] = [w for w in wrongs if w.get("id") != wrong.get("id")]
                        persist()
                        st.success("복습 완료: XP 15, 기억의 조각 1")
                        st.rerun()
                    else:
                        st.warning("아직 정답이 아닙니다.")
                        st.info("해설: " + str(wrong.get("explanation", "")))


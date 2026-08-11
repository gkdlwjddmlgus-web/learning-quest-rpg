from game_core import *


def render_quest_tab() -> None:
    active_world = get_active_learning_world()

    if active_world is None:
        st.warning(
            "활성 학습 월드가 없습니다. 먼저 🌍 학습 월드 탭에서 새 월드를 생성하세요."
        )
    else:
        subjects = active_world.get("subjects", [])

        if not subjects:
            st.warning("현재 학습 월드에 세부 학습 분야가 없습니다.")
        else:
            subject_by_name = {
                str(subject.get("name", subject.get("subject_id", "분야"))): subject
                for subject in subjects
            }
            subject_names = list(subject_by_name.keys())

            # 월드가 바뀌면 이전 월드의 선택값과 문제를 제거한다.
            current_world_id = int(active_world["id"])
            if st.session_state.get("quest_world_id") != current_world_id:
                st.session_state.quest_world_id = current_world_id
                st.session_state.selected_category = subject_names[0]
                reset_question()

            if st.session_state.selected_category not in subject_names:
                st.session_state.selected_category = subject_names[0]
                reset_question()

            world_name_safe = html.escape(str(active_world.get("world_name", "학습 월드")))
            topic_safe = html.escape(str(active_world.get("topic", "")))
            goal_safe = html.escape(str(active_world.get("goal", "") or "핵심 개념 학습"))
            st.markdown(
                '<div class="quest-page-head">'
                '<div class="quest-page-eyebrow">QUEST BOARD</div>'
                f'<div class="quest-page-title">📜 {world_name_safe} 퀘스트</div>'
                f'<div class="quest-page-copy">{topic_safe} · 목표: {goal_safe}</div>'
                '</div>',
                unsafe_allow_html=True,
            )

            quest_recommendation = build_weakness_recommendation(active_world)
            if quest_recommendation:
                rec_name = html.escape(str(quest_recommendation["subject_name"]))
                rec_diff = html.escape(str(quest_recommendation["difficulty"]))
                rec_reason = html.escape(str(quest_recommendation.get("reason", "")))
                rec_attempts = int(quest_recommendation.get("attempts", 0) or 0)
                rec_accuracy = (
                    f"{float(quest_recommendation['accuracy']) * 100:.1f}%"
                    if rec_attempts and quest_recommendation.get("accuracy") is not None
                    else "진단 전"
                )
                st.markdown(
                    '<div class="quest-recommend">'
                    '<div class="quest-recommend-top">'
                    '<div>'
                    '<div class="quest-recommend-eyebrow">RECOMMENDED QUEST</div>'
                    f'<div class="quest-recommend-title">🎯 {rec_name}</div>'
                    '</div>'
                    '<div class="quest-recommend-badge">학습 기록 기반</div>'
                    '</div>'
                    '<div class="quest-recommend-stats">'
                    f'<div class="quest-recommend-stat"><span>추천 분야</span><b>{rec_name}</b></div>'
                    f'<div class="quest-recommend-stat"><span>추천 난이도</span><b>{rec_diff}</b></div>'
                    f'<div class="quest-recommend-stat"><span>현재 정답률</span><b>{rec_accuracy}</b></div>'
                    '</div>'
                    f'<div class="quest-recommend-reason">{rec_reason}</div>'
                    '</div>',
                    unsafe_allow_html=True,
                )
                rec_space, rec_action = st.columns([3.2, 1])
                with rec_action:
                    if st.button(
                        "추천 설정 반영",
                        key=f"apply_recommendation_{current_world_id}",
                        width="stretch",
                    ):
                        st.session_state.selected_category = quest_recommendation["subject_name"]
                        st.session_state.selected_difficulty = quest_recommendation["difficulty"]
                        reset_question()
                        st.rerun()

            with st.container(border=True):
                st.markdown(
                    '<div class="quest-prep-head">'
                    '<div class="quest-prep-eyebrow">QUEST PREPARATION</div>'
                    '<div class="quest-prep-title">🧭 이번 퀘스트 설정</div>'
                    '<div class="quest-prep-copy">학습할 분야와 난이도를 선택하면 현재 월드의 문제은행에서 퀘스트를 준비합니다.</div>'
                    '</div>',
                    unsafe_allow_html=True,
                )

                c1, c2 = st.columns(2)
                category = c1.selectbox(
                    "세부 학습 분야",
                    subject_names,
                    index=subject_names.index(st.session_state.selected_category),
                )
                difficulty = c2.selectbox(
                    "난이도",
                    DIFFICULTIES,
                    index=DIFFICULTIES.index(st.session_state.selected_difficulty),
                )

                if (
                    category != st.session_state.selected_category
                    or difficulty != st.session_state.selected_difficulty
                ):
                    st.session_state.selected_category = category
                    st.session_state.selected_difficulty = difficulty
                    reset_question()
                    st.rerun()

                selected_subject = subject_by_name[category]

                with st.expander("📚 선택한 학습 영역 설명", expanded=False):
                    st.write(
                        selected_subject.get(
                            "description",
                            "이 분야에 대한 설명이 없습니다.",
                        )
                    )

                if st.session_state.pool_message:
                    st.caption(f"📚 {st.session_state.pool_message}")

                if st.button(
                    "⚔️ 이 설정으로 새 퀘스트 받기",
                    type="primary",
                    width="stretch",
                ):
                    reset_question()
                    st.rerun()

            if st.session_state.current_question is None:
                with st.spinner(
                    f"{category} 문제은행을 확인하고 있습니다..."
                ):
                    st.session_state.current_question = load_question(
                        category=category,
                        difficulty=difficulty,
                        world=active_world,
                        subject=selected_subject,
                    )

            q = st.session_state.current_question

            if not q:
                st.warning(
                    "사용 가능한 문제가 없습니다. Gemini 생성 오류가 표시되었다면 해당 메시지를 확인하세요."
                )
            else:
                st.markdown(
                    """
                    <style>
                    /* Unified quest card: question, answer and action stay in one visual flow. */
                    div[data-testid="stRadio"] {margin-top:.05rem; margin-bottom:.15rem;}
                    div[data-testid="stRadio"] > div {gap:.04rem;}
                    div[data-testid="stRadio"] label {padding-top:.04rem; padding-bottom:.04rem;}
                    .quest-unified-head{margin:.05rem 0 .65rem;}
                    .quest-unified-title{font-size:1.06rem;font-weight:900;line-height:1.35;margin-top:.10rem;}
                    .quest-unified-meta{display:flex;flex-wrap:wrap;gap:.32rem .75rem;margin-top:.30rem;font-size:.70rem;font-weight:700;opacity:.72;}
                    .quest-unified-meta span{white-space:nowrap;}
                    div[data-testid="stVerticalBlockBorderWrapper"] .question-box{margin:.25rem 0 .55rem;padding:.90rem 1rem;font-size:1.02rem;line-height:1.65;}
                    </style>
                    """,
                    unsafe_allow_html=True,
                )

                with st.container(border=True):
                    display_category = q.get("_display_category", category)
                    difficulty_icon = (
                        "🟢" if q["difficulty"] == "쉬움"
                        else "🟡" if q["difficulty"] == "보통"
                        else "🔴"
                    )
                    display_category_safe = html.escape(str(display_category))
                    difficulty_safe = html.escape(str(q.get("difficulty", "")))
                    world_name_safe = html.escape(str(active_world.get("world_name", "학습 월드")))
                    xp_value = int(q.get("xp", 0) or 0)

                    st.markdown(
                        '<div class="quest-unified-head">'
                        '<div class="quest-card-eyebrow">ACTIVE QUEST</div>'
                        f'<div class="quest-unified-title">{difficulty_icon} {display_category_safe} 퀘스트</div>'
                        '<div class="quest-unified-meta">'
                        f'<span>🎚️ {difficulty_safe}</span>'
                        f'<span>✨ {xp_value} XP</span>'
                        '<span>🎫 전투권 +1</span>'
                        f'<span>🌍 {world_name_safe}</span>'
                        '</div>'
                        '</div>',
                        unsafe_allow_html=True,
                    )

                    # 문제와 답안을 같은 바깥 카드 안에서 이어서 보여준다.
                    render_hint = f"{active_world.get('topic', '')} {display_category}"
                    render_question(q["question"], render_hint, connected=False)

                    effective_qtype = get_effective_question_type(q)

                    if effective_qtype == "short_answer":
                        expected_answers = parse_short_answers(q.get("answer", ""))
                        multi_slot = is_multi_slot_short_answer(
                            q.get("question", ""),
                            expected_answers,
                        )

                        # 정답 자체를 예시로 노출하지 않고 입력 형식만 안내한다.
                        placeholder = get_short_answer_placeholder(
                            q.get("question", ""),
                            expected_answers,
                        )

                        answer_text = st.text_input(
                            "단답",
                            placeholder=placeholder,
                            disabled=st.session_state.answer_checked,
                            label_visibility="collapsed",
                        )

                        if multi_slot:
                            st.caption("여러 빈칸 문제입니다. 정답을 순서대로 입력하세요. 줄바꿈, 쉼표 또는 / 로 구분할 수 있습니다.")
                        elif len(expected_answers) > 1:
                            st.caption("허용되는 정답 표현 중 하나만 입력하면 됩니다.")

                        submit_left, submit_center, submit_right = st.columns([1.35, 1.6, 1.35])
                        with submit_center:
                            submit_answer = st.button(
                                "답변 제출",
                                type="primary",
                                disabled=st.session_state.answer_checked,
                                width="stretch",
                            )
                        if submit_answer:
                            if not str(answer_text).strip():
                                st.session_state.answer_is_correct = None
                                st.session_state.answer_message = "답변을 입력해주세요."
                                is_correct = None
                            else:
                                is_correct, feedback_message = evaluate_short_answer(
                                    user_answer=answer_text,
                                    correct_answer=q.get("answer", ""),
                                    question_text=q.get("question", ""),
                                )

                            if is_correct is True:
                                st.session_state.answer_checked = True
                                st.session_state.answer_is_correct = True
                                st.session_state.answer_message = (
                                    "\n\n".join(complete_question(q, answer_text))
                                    + "\n\n✅ 정답"
                                )
                                st.balloons()
                            elif is_correct is False:
                                # 최초 오답은 그 자리에서 다시 풀게 하지 않는다.
                                # 일반 문제은행에서는 소진 처리하고 오답 던전에서 복습한다.
                                log_question_attempt(q, answer_text, False, xp_earned=0, attempt_type="quest")
                                save_wrong_question(q)
                                mark_question_as_solved(int(q["id"]))
                                st.session_state.answer_checked = True
                                st.session_state.answer_is_correct = False
                                st.session_state.answer_message = (
                                    "❌ 오답입니다. 오답 던전에 저장했습니다. 정답과 해설은 복습할 때 확인할 수 있습니다."
                                )

                    elif effective_qtype == "subjective":
                        # 과거 DB에 남아 있는 subjective 문제 호환용.
                        # 모범답안이 짧으면 단답 입력 UI로 처리한다.
                        legacy_answer = str(q.get("answer", ""))
                        if len(legacy_answer.strip()) <= 80:
                            answer_text = st.text_input(
                                "단답",
                                placeholder="짧은 정답을 입력하세요",
                                disabled=st.session_state.answer_checked,
                                label_visibility="collapsed",
                            )
                        else:
                            answer_text = st.text_area(
                                "답변",
                                height=160,
                                disabled=st.session_state.answer_checked,
                                label_visibility="collapsed",
                            )

                        submit_left, submit_center, submit_right = st.columns([1.35, 1.6, 1.35])
                        with submit_center:
                            submit_answer = st.button(
                                "답변 제출",
                                type="primary",
                                disabled=st.session_state.answer_checked,
                                width="stretch",
                            )
                        if submit_answer:
                            if not str(answer_text).strip():
                                st.session_state.answer_is_correct = None
                                st.session_state.answer_message = "답변을 입력해주세요."
                                is_correct = None
                            else:
                                is_correct, feedback_message = evaluate_subjective_answer(
                                    user_answer=answer_text,
                                    correct_answer=q.get("answer", ""),
                                    keywords=q.get("keywords"),
                                )

                            if is_correct is True:
                                st.session_state.answer_checked = True
                                st.session_state.answer_is_correct = True
                                st.session_state.answer_message = (
                                    "\n\n".join(complete_question(q, answer_text))
                                    + "\n\n✅ 정답"
                                )
                                st.balloons()
                            elif is_correct is False:
                                log_question_attempt(q, answer_text, False, xp_earned=0, attempt_type="quest")
                                save_wrong_question(q)
                                mark_question_as_solved(int(q["id"]))
                                st.session_state.answer_checked = True
                                st.session_state.answer_is_correct = False
                                st.session_state.answer_message = (
                                    "❌ 오답입니다. 오답 던전에 저장했습니다. 정답과 해설은 복습할 때 확인할 수 있습니다."
                                )

                    else:
                        options = [
                            option
                            for option in (q.get("options") or [])
                            if option != st.session_state.hidden_option
                        ]

                        selected = st.radio(
                            "정답 선택",
                            options,
                            index=None,
                            disabled=st.session_state.answer_checked,
                            label_visibility="collapsed",
                        )

                        submit_left, submit_center, submit_right = st.columns([1.35, 1.6, 1.35])
                        with submit_center:
                            submit_answer = st.button(
                                "정답 제출",
                                type="primary",
                                disabled=st.session_state.answer_checked,
                                width="stretch",
                            )
                        if submit_answer:
                            if selected == q["answer"]:
                                st.session_state.answer_checked = True
                                st.session_state.answer_is_correct = True
                                st.session_state.answer_message = (
                                    "\n\n".join(complete_question(q, selected))
                                    + "\n\n✅ 정답"
                                )
                                st.balloons()

                            elif selected is None:
                                st.session_state.answer_message = "답을 선택하세요."

                            else:
                                log_question_attempt(q, selected, False, xp_earned=0, attempt_type="quest")
                                save_wrong_question(q)
                                mark_question_as_solved(int(q["id"]))
                                st.session_state.answer_checked = True
                                st.session_state.answer_is_correct = False
                                st.session_state.answer_message = (
                                    "❌ 오답입니다. 오답 던전에 저장했습니다. 정답과 해설은 복습할 때 확인할 수 있습니다."
                                )

                    if st.session_state.answer_message:
                        if st.session_state.answer_is_correct is True:
                            st.success(st.session_state.answer_message)
                            st.info("해설: " + q["explanation"])
                        elif st.session_state.answer_is_correct is False:
                            st.warning(st.session_state.answer_message)
                        else:
                            st.warning(st.session_state.answer_message)

                    if st.session_state.answer_checked:
                        next_left, next_center, next_right = st.columns([1.35, 1.6, 1.35])
                        with next_center:
                            next_quest = st.button(
                                "➡️ 다음 퀘스트",
                                width="stretch",
                            )
                        if next_quest:
                            reset_question()
                            st.rerun()


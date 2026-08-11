from core import *


def render_profile_tab() -> None:
    active_world = get_active_learning_world()
    st.subheader("🏘️ 학습 거점")
    if active_world is None:
        st.info("학습 월드를 생성하면 분야별 건물이 이곳에 나타납니다.")
    else:
        buildings = build_subject_buildings(active_world)
        st.caption("학습 기록을 건물 성장 상태로 번역합니다. 숫자 피드백 대신 어떤 분야를 강화해야 하는지 게임처럼 확인할 수 있습니다.")
        for row_start in range(0, len(buildings), 2):
            cols = st.columns(2)
            for offset, col in enumerate(cols):
                idx = row_start + offset
                if idx >= len(buildings):
                    continue
                b = buildings[idx]
                with col:
                    acc_text = "기록 없음" if b["attempts"] == 0 else f"정답률 {b['accuracy']:.0%} · {b['attempts']}회"
                    st.markdown(
                        f'<div class="game-card"><div style="font-size:.72rem;letter-spacing:.12em;color:#7b8190;font-weight:700;">LEARNING BUILDING</div>'
                        f'<div style="font-size:1.05rem;font-weight:800;margin:.25rem 0;">🏛️ {html.escape(b["building_name"])} · Lv.{b["level"]}</div>'
                        f'<div style="font-size:.84rem;color:#687080;">{html.escape(acc_text)} · {html.escape(b["state"])}</div>'
                        f'<div style="margin-top:.65rem;line-height:1.55;">{html.escape(b["message"])}</div></div>',
                        unsafe_allow_html=True,
                    )
        st.divider()

    st.subheader("직업과 칭호")
    if st.session_state.level >= 5 and st.session_state.extra["job"] == "미전직":
        selected_job = st.selectbox("전직 선택", [x for x in CLASS_INFO if x != "미전직"])
        st.caption(CLASS_INFO[selected_job]["description"])
        if st.button("전직", type="primary"):
            st.session_state.extra["job"] = selected_job; persist(); st.rerun()
    else:
        st.write(f"현재 직업: **{st.session_state.extra['job']}**")
        st.caption(CLASS_INFO[st.session_state.extra['job']]["description"])
    title = st.selectbox("표시 칭호", st.session_state.extra["titles"], index=st.session_state.extra["titles"].index(st.session_state.extra["selected_title"]))
    if title != st.session_state.extra["selected_title"]:
        st.session_state.extra["selected_title"] = title; persist(); st.rerun()
    st.divider(); st.subheader("업적")
    for name, data in ACHIEVEMENTS.items():
        done = name in st.session_state.extra["achievements"]
        st.write(f"{'✅' if done else '⬜'} **{name}** — 보상: {data['reward']}")
    st.divider(); st.subheader("세트 효과")
    st.write("2세트: 공격력 +3 · 3세트: 방어력 +3 · 5세트: 경험치 +10%")
    st.divider(); st.subheader("최근 랜덤 이벤트")
    for event in reversed(st.session_state.extra["event_log"][-5:]):
        st.write(f"• {event['time']} — {event['text']}")

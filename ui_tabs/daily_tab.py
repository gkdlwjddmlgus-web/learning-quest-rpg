from core import *


def render_daily_tab() -> None:
    st.subheader("오늘의 퀘스트")
    daily_world = get_active_learning_world()
    p = get_daily_world_progress(daily_world)

    if daily_world is not None:
        st.caption(f"현재 월드: {daily_world['world_name']} · 오늘의 집중 분야: {p.get('focus_subject_name', '선택 분야')}")
        focus_label = f"{p.get('focus_subject_name', '집중 분야')} 정답"
    else:
        focus_label = "집중 분야 정답"

    tasks = [
        ("문제 정답", p["correct"], 3),
        (focus_label, p["focus"], 1),
        ("몬스터 처치/포획", p["battles"], 1),
    ]
    for name, value, target in tasks:
        st.write(f"**{name}** {min(value, target)}/{target}")
        st.progress(min(value / target, 1.0))

    st.write("보상: XP 50 · 전투권 2 · 회복 물약 1")
    if st.button("일일 보상 받기", disabled=not daily_complete(daily_world) or daily_claimed(daily_world), type="primary"):
        st.session_state.event_message = claim_daily(daily_world)
        st.rerun()
    if daily_claimed(daily_world):
        st.success("오늘 이 월드의 일일 보상을 받았습니다.")
    if st.session_state.event_message:
        st.info(st.session_state.event_message)
    st.divider()
    st.subheader("연속 학습")
    st.metric("🔥 연속 학습", f"{st.session_state.extra['streak']}일")
    st.caption("7일 연속 학습 시 희귀 장비 업적 보상")


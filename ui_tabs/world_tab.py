from game_core import *


def render_world_tab() -> None:
        st.subheader("🌍 학습 월드")
        st.caption("현재 월드를 확인하거나 새 학습 세계를 생성합니다.")

        worlds = get_learning_worlds()
        active_world = get_active_learning_world()

        if worlds:
            world_ids = [world["id"] for world in worlds]
            active_id = active_world["id"] if active_world else world_ids[0]
            default_index = world_ids.index(active_id) if active_id in world_ids else 0

            selector_col, selector_hint_col = st.columns([4.8, 1.2])
            selected_world_id = selector_col.selectbox(
                "월드 선택",
                world_ids,
                index=default_index,
                format_func=lambda world_id: next(
                    (
                        f"{'✅ ' if world.get('is_active') else ''}{world['world_name']} · {world['topic']}"
                        for world in worlds
                        if world["id"] == world_id
                    ),
                    str(world_id),
                ),
                key="learning_world_selector",
                label_visibility="collapsed",
            )
            selector_hint_col.caption("WORLD SELECT")

            selected_world = next(
                world for world in worlds
                if world["id"] == selected_world_id
            )

            world_name = html.escape(str(selected_world.get("world_name", "이름 없는 월드")))
            world_topic = html.escape(str(selected_world.get("topic", "")))
            learner_level_text = html.escape(str(selected_world.get("learner_level", "")))
            goal_text = html.escape(str(selected_world.get("goal", "") or "핵심 개념을 익히고 꾸준히 성장하기"))
            description_text = html.escape(str(selected_world.get("world_data", {}).get("world_description", "") or "이 학습 주제를 탐험하며 새로운 지역과 도전을 만나보세요."))
            subject_count = len(selected_world.get("subjects", []))
            region_count = len(selected_world.get("regions", []))
            monster_count = len(selected_world.get("monsters", []))
            active_badge = "● ACTIVE WORLD" if selected_world.get("is_active") else "○ SELECTED WORLD"

            world_card_html = f'''<div class="world-hero">
    <div class="world-hero-top">
    <div>
    <div class="world-eyebrow">LEARNING WORLD</div>
    <div class="world-name">🌍 {world_name}</div>
    <div class="world-meta">{world_topic} · {learner_level_text}</div>
    </div>
    <div class="world-badge">{active_badge}</div>
    </div>
    <div class="world-goal"><b>🎯 목표</b><br>{goal_text}</div>
    <div class="world-description">{description_text}</div>
    <div class="world-content-strip">
    <div class="world-content-item">📚 <b>{subject_count}</b>개 학습 영역</div>
    <div class="world-content-item">🗺️ <b>{region_count}</b>개 탐험 지역</div>
    <div class="world-content-item">👾 <b>{monster_count}</b>종 몬스터</div>
    </div>
    </div>'''
            st.markdown(world_card_html, unsafe_allow_html=True)

            if not selected_world.get("is_active"):
                if st.button("🌍 이 월드로 전환", type="primary", width="stretch"):
                    if set_active_learning_world(selected_world_id):
                        st.session_state.current_question = None
                        st.session_state.answer_checked = False
                        st.session_state.answer_is_correct = None
                        st.session_state.answer_message = ""
                        st.success("활성 학습 월드를 변경했습니다.")
                        st.rerun()
                    else:
                        st.error("학습 월드를 변경하지 못했습니다.")

            nav1, nav2, nav3 = st.columns(3)

            with nav1:
                st.markdown(
                    f'<div class="world-nav-card"><div class="world-nav-title">📚 학습 영역</div><div class="world-nav-copy">{subject_count}개의 세부 분야와 학습 방향</div></div>',
                    unsafe_allow_html=True,
                )
                with st.expander("학습 영역 열어보기"):
                    for index, subject in enumerate(selected_world.get("subjects", []), start=1):
                        st.markdown(f"**{index}. {subject.get('name', '이름 없음')}**")
                        st.caption(subject.get("description", ""))

            with nav2:
                st.markdown(
                    f'<div class="world-nav-card"><div class="world-nav-title">🗺️ 탐험 지역</div><div class="world-nav-copy">{region_count}개의 지역과 탐험 배경</div></div>',
                    unsafe_allow_html=True,
                )
                with st.expander("탐험 지역 열어보기"):
                    for index, region in enumerate(selected_world.get("regions", []), start=1):
                        st.markdown(f"**{index}. {region.get('name', '이름 없음')}**")
                        st.caption(region.get("description", ""))

            with nav3:
                boss = selected_world.get("world_data", {}).get("boss")
                boss_suffix = " + 보스" if boss else ""
                st.markdown(
                    f'<div class="world-nav-card"><div class="world-nav-title">👾 몬스터 도감</div><div class="world-nav-copy">{monster_count}종 몬스터{boss_suffix}</div></div>',
                    unsafe_allow_html=True,
                )
                with st.expander("몬스터 도감 열어보기"):
                    selected_world_id_int = int(selected_world["id"])
                    captured_monster_ids = {
                        str(monster.get("monster_id"))
                        for monster in st.session_state.extra.get("captured_monsters", [])
                        if monster.get("world_id") in (None, selected_world_id_int)
                        and monster.get("monster_id")
                    }

                    world_monsters = selected_world.get("monsters", []) or []
                    regions = selected_world.get("regions", []) or []

                    if not world_monsters:
                        st.caption("이 월드에는 아직 등록된 몬스터가 없습니다.")
                    else:
                        captured_count = sum(
                            1
                            for monster in world_monsters
                            if str(monster.get("monster_id")) in captured_monster_ids
                        )
                        st.caption(f"수집 진행도: {captured_count}/{len(world_monsters)}")

                        for region in regions:
                            subject_id = str(region.get("subject_id", ""))
                            region_monsters = [
                                monster
                                for monster in world_monsters
                                if str(monster.get("subject_id", "")) == subject_id
                            ]
                            if not region_monsters:
                                continue

                            st.markdown(f"**🗺️ {region.get('name', '이름 없는 지역')}**")
                            monster_badges = []
                            for monster in region_monsters:
                                monster_id = str(monster.get("monster_id", ""))
                                captured_mark = "✅" if monster_id in captured_monster_ids else "⬜"
                                monster_name = html.escape(str(monster.get("name", "이름 없음")))
                                monster_badges.append(
                                    f'<span style="display:inline-block; white-space:nowrap; margin:0 0.45rem 0.35rem 0;">'
                                    f'{captured_mark} {monster_name}</span>'
                                )
                            st.markdown(
                                '<div style="line-height:1.9;">' + ''.join(monster_badges) + '</div>',
                                unsafe_allow_html=True,
                            )

                        unassigned_monsters = [
                            monster
                            for monster in world_monsters
                            if not any(
                                str(monster.get("subject_id", ""))
                                == str(region.get("subject_id", ""))
                                for region in regions
                            )
                        ]
                        if unassigned_monsters:
                            st.markdown("**🌫️ 기타 지역**")
                            monster_badges = []
                            for monster in unassigned_monsters:
                                monster_id = str(monster.get("monster_id", ""))
                                captured_mark = "✅" if monster_id in captured_monster_ids else "⬜"
                                monster_name = html.escape(str(monster.get("name", "이름 없음")))
                                monster_badges.append(
                                    f'<span style="display:inline-block; white-space:nowrap; margin:0 0.45rem 0.35rem 0;">'
                                    f'{captured_mark} {monster_name}</span>'
                                )
                            st.markdown(
                                '<div style="line-height:1.9;">' + ''.join(monster_badges) + '</div>',
                                unsafe_allow_html=True,
                            )

                    if boss:
                        st.divider()
                        st.write(f"👑 **보스: {boss.get('name', '이름 없음')}**")
                        st.caption(boss.get("description", ""))
        else:
            st.info("아직 생성된 학습 월드가 없습니다. 아래에서 첫 월드를 만들어보세요.")

        st.divider()
        st.markdown(
            """<div class="world-create-head">
    <div class="world-create-eyebrow">NEW ADVENTURE</div>
    <div class="world-create-title">새로운 학습 세계가 필요하신가요?</div>
    <div class="world-create-copy">월드 생성은 게임 홈이 아닌 세계의 문에서 진행합니다.</div>
    </div>""",
            unsafe_allow_html=True,
        )
        if st.button("✨ 세계의 문에서 새 월드 생성", width="stretch", key="open_world_gate_create"):
            from onboarding.world_gate import open_world_gate
            open_world_gate("create")


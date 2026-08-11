from core import *


def render_monster_tab() -> None:
    active_monster_world = get_active_learning_world()
    captured_all = st.session_state.extra["captured_monsters"]
    dex = st.session_state.extra["monster_dex"]

    if active_monster_world is None:
        st.info("먼저 학습 월드를 생성하거나 선택하세요.")
    else:
        active_world_id = int(active_monster_world["id"])
        captured = [
            monster for monster in captured_all
            if monster.get("world_id") in (None, active_world_id)
        ]
        catalog = dynamic_monster_catalog(active_monster_world)

        st.subheader(f"📕 {active_monster_world['world_name']} 몬스터")
        st.caption(
            "현재 활성 학습 월드의 몬스터만 도감에 표시됩니다. "
            "포획한 몬스터는 학습 분야 경험치 보너스를 제공합니다."
        )

        st.subheader("활성 몬스터 팀")
        options = [monster["instance_id"] for monster in captured]

        # 다른 월드의 몬스터가 기존 팀 슬롯에 들어 있다면 비운다.
        valid_ids = set(options)
        for idx, instance_id in enumerate(st.session_state.extra["active_monster_team"]):
            if instance_id is not None and instance_id not in valid_ids:
                st.session_state.extra["active_monster_team"][idx] = None

        for team_index in range(3):
            current = st.session_state.extra["active_monster_team"][team_index]
            valid_options = [None] + options
            current_index = valid_options.index(current) if current in valid_options else 0
            selected = st.selectbox(
                f"팀 슬롯 {team_index + 1}",
                valid_options,
                index=current_index,
                format_func=lambda value: (
                    "비어 있음"
                    if value is None
                    else f"{get_captured_monster(value)['emoji']} "
                         f"{get_captured_monster(value)['name']} · "
                         f"{get_captured_monster(value)['nature']}"
                ),
                key=f"team_slot_{team_index}",
            )

            if selected != current:
                other_slots = [
                    x for idx, x in enumerate(st.session_state.extra["active_monster_team"])
                    if idx != team_index
                ]
                if selected is not None and selected in other_slots:
                    st.warning("같은 몬스터를 두 슬롯에 동시에 편성할 수 없습니다.")
                else:
                    st.session_state.extra["active_monster_team"][team_index] = selected
                    persist()
                    st.rerun()

        if team_monsters():
            st.write("팀 학습 보너스")
            subject_names = [
                str(subject.get("name", subject.get("subject_id", "")))
                for subject in active_monster_world.get("subjects", [])
            ]
            for subject_name in subject_names:
                bonus = team_xp_bonus(subject_name)
                if bonus > 0:
                    st.write(f"• {subject_name} 경험치 +{bonus:.0%}")

        st.divider()
        st.subheader(f"보유 몬스터 · {len(captured)}마리")
        if not captured:
            st.info("사냥터나 던전에서 몬스터의 체력을 낮춘 뒤 데이터볼로 포획해보세요.")
        else:
            for monster in captured:
                with st.expander(
                    f"{monster['emoji']} {monster['name']} · "
                    f"{monster['rarity']} · {monster['nature']}"
                ):
                    c1, c2, c3 = st.columns(3)
                    c1.metric("공격 개체값", monster["attack_iv"])
                    c2.metric("방어 개체값", monster["defense_iv"])
                    c3.metric("학습 개체값", monster["learning_iv"])
                    st.write(
                        f"학습 분야: **{monster['category']}** · "
                        f"팀 편성 효과: 경험치 +"
                        f"{monster['xp_bonus'] + monster.get('nature_xp_add', 0):.0%}"
                    )
                    st.caption(f"포획 시각: {monster['captured_at']}")

        st.divider()
        st.subheader("몬스터 도감")

        world_id = int(active_monster_world["id"])
        catalog_records = []
        for monster in catalog:
            monster_id = str(monster.get("monster_id"))
            dex_key = f"world_{world_id}__{monster_id}"
            record = dex.get(dex_key, {"seen": 0, "captured": 0})
            catalog_records.append((monster, record))

        discovered = sum(1 for _, record in catalog_records if record.get("seen", 0) > 0)
        caught_species = sum(1 for monster, record in catalog_records if not monster.get("boss") and record.get("captured", 0) > 0)
        capturable_count = sum(1 for monster, _ in catalog_records if not monster.get("boss"))

        d1, d2, d3 = st.columns(3)
        d1.metric("발견", f"{discovered}/{len(catalog_records)}")
        d2.metric("포획 종", f"{caught_species}/{capturable_count}")
        d3.metric("총 포획", len(captured))

        subjects = world_subject_map(active_monster_world)
        for monster, record in catalog_records:
            is_boss = bool(monster.get("boss"))
            if record.get("seen", 0) <= 0:
                st.write("⬛ **???** — 아직 발견하지 못했습니다.")
                continue

            rarity = "영웅" if is_boss else str(monster.get("rarity", "일반"))
            emoji = "👑" if is_boss else rarity_emoji(rarity)
            subject_id = str(monster.get("subject_id", ""))
            subject_name = str(subjects.get(subject_id, {}).get("name", subject_id))
            capture_text = (
                "🚫 포획 불가 보스"
                if is_boss
                else ("✅ 포획" if record.get("captured", 0) > 0 else "👁️ 발견")
            )
            st.write(
                f"{emoji} **{monster.get('name', '몬스터')}** · {rarity} · "
                f"{subject_name} · {capture_text} · "
                f"조우 {record.get('seen', 0)}회 · 포획 {record.get('captured', 0)}회"
            )


from game_core import *


def render_battle_tab() -> None:
    active_battle_world = get_active_learning_world()

    if active_battle_world is None:
        st.info("먼저 🌍 학습 월드에서 학습 월드를 생성하거나 선택하세요.")
    else:
        regions = active_battle_world.get("regions", [])
        world_key = str(active_battle_world["id"])
        st.subheader(f"⚔️ {active_battle_world['world_name']} 탐험")
        st.caption(
            "일반 사냥터는 횟수 제한이 없고, 일일 던전은 하루 3회까지 입장할 수 있습니다. "
            "두 모드 모두 현재 학습 월드에서 AI가 만든 지역과 몬스터를 사용합니다."
        )

        if not st.session_state.monster:
            hp_current = int(st.session_state.player_hp)
            hp_maximum = int(max_hp())
            ticket_count = int(st.session_state.battle_tickets)
            potion_total = int(potion_count())
            ball_basic = int(capture_item_count(BASIC_BALL_ID))
            ball_great = int(capture_item_count(GREAT_BALL_ID))
            ball_ultra = int(capture_item_count(ULTRA_BALL_ID))

            st.markdown(
                f'<div class="battle-ready-card">'
                f'<div class="battle-ready-eyebrow">ADVENTURE STATUS</div>'
                f'<div class="battle-ready-title">⚔️ 탐험 준비</div>'
                f'<div class="battle-ready-grid">'
                f'<div class="battle-ready-stat"><div class="battle-ready-label">❤️ HP</div><div class="battle-ready-value">{hp_current} / {hp_maximum}</div></div>'
                f'<div class="battle-ready-stat"><div class="battle-ready-label">🎫 전투권</div><div class="battle-ready-value">{ticket_count}</div></div>'
                f'<div class="battle-ready-stat"><div class="battle-ready-label">🧪 물약</div><div class="battle-ready-value">{potion_total}</div></div>'
                f'<div class="battle-ready-stat"><div class="battle-ready-label">⚪ 데이터볼</div><div class="battle-ready-value">{ball_basic + ball_great + ball_ultra}</div></div>'
                f'</div>'
                f'<div class="battle-ball-line">포획 도구 · 일반 {ball_basic} · 고급 {ball_great} · 정제 {ball_ultra}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

            action_left, action_right = st.columns(2)
            if action_left.button(
                "🏕️ 휴식 · 전투권 1",
                disabled=st.session_state.player_hp >= max_hp() or st.session_state.battle_tickets < 1,
                width="stretch",
            ):
                st.session_state.event_message = rest()
                st.rerun()
            if action_right.button(
                "🧪 물약 사용",
                disabled=potion_count() <= 0 or st.session_state.player_hp >= max_hp(),
                width="stretch",
            ):
                st.session_state.event_message = use_potion()
                st.rerun()

            if st.session_state.event_message:
                st.info(st.session_state.event_message)

            hunt_tab, daily_dungeon_tab = st.tabs(["🌿 일반 사냥터", "🏰 일일 던전"])

            with hunt_tab:
                st.markdown(
                    '<div class="hunt-section-head">'
                    '<div class="hunt-section-eyebrow">FREE HUNT</div>'
                    '<div class="hunt-section-title">🌿 횟수 제한 없는 일반 사냥</div>'
                    '<div class="hunt-section-copy">원하는 지역을 골라 반복 탐험합니다. 전투 1회마다 전투권 1개를 사용하며 기본 드랍률이 적용됩니다.</div>'
                    '</div>',
                    unsafe_allow_html=True,
                )

                if not regions:
                    st.warning("현재 월드에 생성된 지역이 없습니다.")
                else:
                    subject_map = world_subject_map(active_battle_world)
                    for row_start in range(0, len(regions), 2):
                        region_cols = st.columns(2)
                        for offset, col in enumerate(region_cols):
                            region_index = row_start + offset
                            if region_index >= len(regions):
                                continue

                            region = regions[region_index]
                            idx = region_index + 1
                            pool = world_monsters_for_region(active_battle_world, region)
                            subject_name = subject_map.get(
                                str(region.get("subject_id", "")), {}
                            ).get("name", region.get("subject_id", ""))
                            description = str(region.get("description", ""))
                            monster_count = len(pool)

                            with col:
                                st.markdown(
                                    f'<div class="hunt-region-card">'
                                    f'<div class="hunt-region-title">🌿 {html.escape(str(region.get("name", "미지의 지역")))}</div>'
                                    f'<div class="hunt-region-subject">📚 {html.escape(str(subject_name))}</div>'
                                    f'<div class="hunt-region-meta">👾 출현 몬스터 {monster_count}종</div>'
                                    f'<div class="hunt-region-desc">{html.escape(description)}</div>'
                                    f'</div>',
                                    unsafe_allow_html=True,
                                )

                                if st.button(
                                    "⚔️ 사냥 시작",
                                    key=f"hunt_world_{world_key}_{region.get('region_id', idx)}",
                                    disabled=st.session_state.battle_tickets < 1 or not pool,
                                    width="stretch",
                                ):
                                    st.session_state.battle_tickets -= 1
                                    st.session_state.monster = create_world_monster(
                                        active_battle_world,
                                        region,
                                        encounter_type="hunt",
                                    )
                                    m = st.session_state.monster
                                    st.session_state.battle_log = [
                                        "🎫 전투권 1개 소모",
                                        f"🌿 {region.get('name', '일반 사냥터')}에서 {m['emoji']} {m['name']} 조우",
                                    ]
                                    persist()
                                    st.rerun()

                if st.session_state.battle_tickets < 1:
                    st.warning("전투권이 없습니다. 퀘스트를 완료해 전투권을 획득하세요.")

            with daily_dungeon_tab:
                runs_by_world = st.session_state.extra.setdefault(
                    "daily_dungeon_runs_by_world", {}
                )
                used_runs = int(runs_by_world.get(world_key, 0))
                remaining_runs = max(0, DAILY_DUNGEON_LIMIT - used_runs)

                c1, c2, c3 = st.columns(3)
                c1.metric("오늘 입장", f"{used_runs}/{DAILY_DUNGEON_LIMIT}")
                c2.metric("남은 횟수", remaining_runs)
                c3.metric("던전 XP", f"+{int((DUNGEON_XP_MULTIPLIER - 1) * 100)}%")

                st.success(
                    f"던전 버프: 장비 드랍률 +{int(DUNGEON_EQUIPMENT_DROP_BONUS * 100)}%p · "
                    f"물약 드랍률 +{int(DUNGEON_POTION_DROP_BONUS * 100)}%p · "
                    "데이터볼 드랍률 증가"
                )
                st.caption(
                    "일일 던전 횟수는 학습 월드별 하루 3회이며 날짜가 바뀌면 초기화됩니다. "
                    "입장 시 전투권 1개도 소모됩니다."
                )

                dungeon_entries: list[tuple[str, dict[str, Any] | None, bool]] = [
                    (str(region.get("name", "지역")), region, False)
                    for region in regions
                ]
                boss_template = get_world_boss(active_battle_world)
                if boss_template:
                    dungeon_entries.append((str(boss_template.get("name", "최종 보스")), None, True))

                for idx, (entry_name, region, is_boss) in enumerate(dungeon_entries, start=1):
                    if is_boss:
                        description = str(boss_template.get("description", "")) if boss_template else ""
                        pool_names = str(boss_template.get("name", "최종 보스")) if boss_template else "최종 보스"
                        css = "game-card boss"
                        icon = "👑"
                    else:
                        pool = world_monsters_for_region(active_battle_world, region or {})
                        pool_names = ", ".join(str(m.get("name", "???")) for m in pool) or "출현 몬스터 없음"
                        description = str((region or {}).get("description", ""))
                        css = "game-card"
                        icon = "🏰"

                    st.markdown(
                        f'<div class="{css}"><b>{icon} {html.escape(entry_name)}</b><br>'
                        f'출현: {html.escape(pool_names)}<br>'
                        f'{html.escape(description)}<br>'
                        f'던전 XP 및 드랍률 버프 적용</div>',
                        unsafe_allow_html=True,
                    )

                    disabled = remaining_runs <= 0 or st.session_state.battle_tickets < 1
                    if not is_boss and not world_monsters_for_region(active_battle_world, region or {}):
                        disabled = True

                    if st.button(
                        "보스 던전 입장" if is_boss else "던전 입장",
                        key=f"dynamic_dungeon_{world_key}_{idx}",
                        disabled=disabled,
                        width="stretch",
                    ):
                        st.session_state.battle_tickets -= 1
                        runs_by_world[world_key] = used_runs + 1
                        st.session_state.monster = create_world_monster(
                            active_battle_world,
                            region,
                            encounter_type="dungeon",
                            boss=is_boss,
                        )
                        m = st.session_state.monster
                        st.session_state.battle_log = [
                            "🎫 전투권 1개 소모",
                            f"🏰 일일 던전 입장 ({used_runs + 1}/{DAILY_DUNGEON_LIMIT})",
                            f"{m['emoji']} {m['name']} 조우 · 던전 드랍 버프 적용",
                        ]
                        persist()
                        st.rerun()

        else:
            m = st.session_state.monster

            # 전투 도중 월드를 전환한 경우 이전 월드 전투는 안전하게 종료한다.
            if int(m.get("world_id", active_battle_world["id"])) != int(active_battle_world["id"]):
                st.warning("학습 월드가 변경되어 이전 월드의 전투를 종료했습니다.")
                st.session_state.monster = None
                persist()
                st.rerun()

            available_balls = [
                ball_id for ball_id in CAPTURE_ITEMS
                if capture_item_count(ball_id) > 0
            ]
            selected_ball = st.session_state.get("capture_ball_select")
            if selected_ball not in available_balls:
                selected_ball = st.session_state.get("selected_capture_ball", BASIC_BALL_ID)
            if selected_ball not in available_balls:
                selected_ball = available_balls[0] if available_balls else BASIC_BALL_ID
            st.session_state.selected_capture_ball = selected_ball

            player_hp_ratio = max(0.0, min(1.0, st.session_state.player_hp / max_hp()))
            monster_hp_ratio = max(0.0, min(1.0, m["hp"] / m["max_hp"]))
            player_hp_pct = round(player_hp_ratio * 100, 1)
            monster_hp_pct = round(monster_hp_ratio * 100, 1)
            mode_text = "🏰 일일 던전" if m.get("encounter_type") == "dungeon" else "🌿 일반 사냥"
            region_text = str(m.get("region_name", "미지의 지역"))
            player_title = html.escape(str(st.session_state.extra.get("selected_title", "모험가")))
            player_job = html.escape(str(st.session_state.extra.get("job", "미전직")))
            monster_name = html.escape(str(m.get("name", "몬스터")))
            monster_emoji = html.escape(str(m.get("emoji", "👾")))
            monster_rarity = html.escape(str(m.get("rarity", "일반")))
            monster_element = html.escape(str(m.get("element", "")))
            monster_description = html.escape(str(m.get("description", "")))
            monster_region = html.escape(region_text)
            capture_text = "포획 불가" if m.get("boss") else f"예상 포획률 {capture_probability(m, selected_ball):.0%}"

            pcol, mcol = st.columns(2, gap="medium")
            with pcol:
                st.markdown(
                    '<div class="combat-card">'
                    '<div class="combat-eyebrow">PLAYER</div>'
                    f'<div class="combat-name">🧙 {player_title} · Lv.{st.session_state.level}</div>'
                    f'<div class="combat-meta">{player_job}</div>'
                    '<div class="combat-hp-row"><span>❤️ HP</span>'
                    f'<b>{max(0, st.session_state.player_hp)} / {max_hp()}</b></div>'
                    '<div class="combat-hp-track">'
                    f'<div class="combat-hp-fill-player" style="width:{player_hp_pct}%"></div>'
                    '</div>'
                    '<div class="combat-stat-grid">'
                    f'<div class="combat-stat"><span>⚔️ ATTACK</span><b>{player_attack()}</b></div>'
                    f'<div class="combat-stat"><span>🛡️ DEFENSE</span><b>{player_defense()}</b></div>'
                    '</div>'
                    '</div>',
                    unsafe_allow_html=True,
                )

            with mcol:
                st.markdown(
                    '<div class="combat-card monster">'
                    '<div class="combat-eyebrow">MONSTER</div>'
                    f'<div class="combat-name">{monster_emoji} {monster_name}</div>'
                    f'<div class="combat-meta">{monster_rarity} · {monster_element} · {monster_region}</div>'
                    '<div class="combat-hp-row"><span>❤️ HP</span>'
                    f'<b>{max(0, m["hp"])} / {m["max_hp"]}</b></div>'
                    '<div class="combat-hp-track">'
                    f'<div class="combat-hp-fill-monster" style="width:{monster_hp_pct}%"></div>'
                    '</div>'
                    '<div class="combat-stat-grid">'
                    f'<div class="combat-stat"><span>⚔️ ATTACK</span><b>{m["attack"]}</b></div>'
                    f'<div class="combat-stat"><span>🛡️ DEFENSE</span><b>{m.get("defense", 0)}</b></div>'
                    f'<div class="combat-stat"><span>🎁 REWARD</span><b>{m["xp"]} XP</b></div>'
                    '</div>'
                    f'<div class="combat-capture">🎯 {html.escape(capture_text)}</div>'
                    + (f'<div class="combat-monster-copy">{monster_description}</div>' if monster_description else '')
                    + '</div>',
                    unsafe_allow_html=True,
                )

            st.markdown(
                '<div class="combat-actions-label">BATTLE ACTIONS</div>',
                unsafe_allow_html=True,
            )

            if available_balls and not m.get("boss"):
                ball_col, ball_note_col = st.columns([2, 3], gap="medium")
                with ball_col:
                    selected_ball = st.selectbox(
                        "포획 도구",
                        available_balls,
                        index=available_balls.index(selected_ball),
                        format_func=lambda x: (
                            f"{CAPTURE_ITEMS[x]['icon']} {CAPTURE_ITEMS[x]['name']} "
                            f"({capture_item_count(x)})"
                        ),
                        key="capture_ball_select",
                    )
                    st.session_state.selected_capture_ball = selected_ball
                with ball_note_col:
                    st.markdown(
                        '<div class="combat-ball-note">🎯 포획 버튼은 선택한 데이터볼을 1개 사용합니다.</div>',
                        unsafe_allow_html=True,
                    )
            elif m.get("boss"):
                st.caption("👑 보스 몬스터는 포획할 수 없습니다.")
            else:
                st.caption("⚪ 보유한 데이터볼이 없습니다.")

            # 보스 체력 임계점 학습 이벤트
            if m.get("boss") and st.session_state.get("boss_quiz"):
                q = st.session_state.boss_quiz
                threshold = st.session_state.get("boss_quiz_threshold")
                st.markdown(f"### 📖 보스의 시험 · HP {threshold}%")
                st.caption("정답이면 다음 3회의 공격력이 25% 증가합니다. 오답이어도 추가 전투 패널티는 없습니다.")
                st.markdown(f"**{q.get('question','')}**")
                qtype = get_effective_question_type(q)
                if qtype == "multiple_choice":
                    boss_answer = st.radio("보스 문제 정답", q.get("options") or [], index=None, key=f"boss_answer_{threshold}")
                else:
                    boss_answer = st.text_input("보스 문제 답변", key=f"boss_answer_{threshold}", placeholder=get_short_answer_placeholder(str(q.get("question", "")), parse_short_answers(q.get("answer"))))
                if st.button("✨ 답변 제출", type="primary", key=f"boss_submit_{threshold}"):
                    ok, result = resolve_boss_quiz(q, boss_answer)
                    st.session_state.battle_log.append(result)
                    st.session_state.boss_quiz = None
                    st.session_state.boss_quiz_threshold = None
                    # 문제 해결 후 보스가 한 번 반격한다.
                    received = max(1, m["attack"] + random.randint(-1, 2) - player_defense())
                    st.session_state.player_hp -= received
                    st.session_state.battle_log.append(f"👑 시험 종료 후 반격 · {received} 피해 받음")
                    if st.session_state.player_hp <= 0:
                        st.session_state.player_hp = max_hp()
                        st.session_state.monster = None
                        st.session_state.battle_log.append("💀 패배 · HP 완전 회복")
                    persist()
                    st.rerun()
                return

            a1, a2, a3, a4 = st.columns(4)

            if a1.button("⚔️ 공격", type="primary", width="stretch"):
                crit = random.random() < min(
                    .05 + st.session_state.luck * .02
                    + (.05 if st.session_state.extra["job"] == "SQL 마법사" else 0),
                    .4,
                )
                raw_damage = max(1, player_attack() + random.randint(-2, 3))
                buff_turns = int(st.session_state.extra.get("boss_attack_buff_turns", 0)) if m.get("boss") else 0
                if buff_turns > 0:
                    raw_damage = max(1, round(raw_damage * 1.25))
                    st.session_state.extra["boss_attack_buff_turns"] = buff_turns - 1
                monster_defense = max(0, int(m.get("defense", 0)))
                mitigated_damage = max(1, raw_damage - monster_defense)
                damage = mitigated_damage * (2 if crit else 1)
                before_hp = int(m["hp"])
                m["hp"] -= damage
                st.session_state.battle_log.append(
                    f"⚔️ {damage} 피해 · 몬스터 방어 {monster_defense}"
                    + (" · 치명타" if crit else "")
                )

                crossed_threshold = boss_threshold_crossed(m, before_hp, int(m["hp"]))
                if crossed_threshold and m["hp"] > 0:
                    q = prepare_boss_quiz(active_battle_world, m, crossed_threshold)
                    if q is not None:
                        st.session_state.boss_quiz = q
                        st.session_state.boss_quiz_threshold = crossed_threshold
                        st.session_state.battle_log.append(f"📖 보스가 HP {crossed_threshold}% 시험을 시작합니다.")
                        persist()
                        st.rerun()

                if m["hp"] <= 0:
                    st.session_state.battle_log.append(f"🏆 {m['name']} 처치")
                    reward_xp = (
                        round(m["xp"] * DUNGEON_XP_MULTIPLIER)
                        if m.get("encounter_type") == "dungeon"
                        else m["xp"]
                    )
                    st.session_state.battle_log.extend(
                        gain_xp(reward_xp, m.get("category", ""))
                    )
                    if m.get("encounter_type") == "dungeon":
                        st.session_state.battle_log.append(
                            f"🏰 던전 XP 보너스 적용: {reward_xp} XP"
                        )

                    finish_encounter(m, captured=False)

                    if m.get("boss"):
                        st.session_state.extra["boss_cleared"] = True
                        dynamic_title = f"{active_battle_world['world_name']} 정복자"
                        if dynamic_title not in st.session_state.extra["titles"]:
                            st.session_state.extra["titles"].append(dynamic_title)
                        add_capture_item(ULTRA_BALL_ID, 1)
                        st.session_state.battle_log.append(
                            f"👑 {dynamic_title} 칭호 획득 · 🟣 정제된 데이터볼 1개"
                        )

                    dungeon_bonus = (
                        DUNGEON_EQUIPMENT_DROP_BONUS
                        if m.get("encounter_type") == "dungeon"
                        else 0.0
                    )
                    item = drop_equipment(drop_bonus=dungeon_bonus)
                    if item:
                        got, duplicate = add_item(item)
                        st.session_state.battle_log.append(
                            f"🎁 {got['name']}"
                            + (f" 수량 {got['quantity']}" if duplicate else " 획득")
                        )

                    potion_bonus = (
                        DUNGEON_POTION_DROP_BONUS
                        if m.get("encounter_type") == "dungeon"
                        else 0.0
                    )
                    if random.random() < min(
                        POTION_DROP_CHANCE + st.session_state.luck * .01 + potion_bonus,
                        .90,
                    ):
                        add_item({
                            "item_id": HEALING_POTION_ID,
                            "name": "회복 물약",
                            "item_type": "consumable",
                            "quantity": 1,
                        })
                        st.session_state.battle_log.append("🧪 회복 물약 획득")

                    ball_roll = random.random()
                    ball_bonus = (
                        DUNGEON_BALL_DROP_BONUS
                        if m.get("encounter_type") == "dungeon"
                        else 0.0
                    )
                    if ball_roll < 0.12 + ball_bonus * 0.45:
                        add_capture_item(GREAT_BALL_ID, 1)
                        st.session_state.battle_log.append("🔵 고급 데이터볼 획득")
                    elif ball_roll < 0.42 + ball_bonus:
                        add_capture_item(BASIC_BALL_ID, 1)
                        st.session_state.battle_log.append("⚪ 일반 데이터볼 획득")

                    evaluate_achievements()
                    st.session_state.monster = None

                else:
                    received = max(
                        1,
                        m["attack"] + random.randint(-1, 2) - player_defense(),
                    )
                    st.session_state.player_hp -= received
                    st.session_state.battle_log.append(f"👾 반격 · {received} 피해 받음")
                    if st.session_state.player_hp <= 0:
                        st.session_state.player_hp = max_hp()
                        st.session_state.monster = None
                        st.session_state.battle_log.append("💀 패배 · HP 완전 회복")

                persist()
                st.rerun()

            if a2.button(
                "🎯 포획",
                disabled=m.get("boss") or not available_balls,
                width="stretch",
            ):
                success, message = capture_monster(m, selected_ball)
                st.session_state.battle_log.append(message)
                if success:
                    finish_encounter(m, captured=True)
                    st.session_state.monster = None
                else:
                    received = max(
                        1,
                        m["attack"] + random.randint(-1, 2) - player_defense(),
                    )
                    st.session_state.player_hp -= received
                    st.session_state.battle_log.append(
                        f"👾 포획 실패 후 반격 · {received} 피해 받음"
                    )
                    if st.session_state.player_hp <= 0:
                        st.session_state.player_hp = max_hp()
                        st.session_state.monster = None
                        st.session_state.battle_log.append("💀 패배 · HP 완전 회복")
                persist()
                st.rerun()

            if a3.button(
                "🧪 물약",
                disabled=potion_count() <= 0 or st.session_state.player_hp >= max_hp(),
                width="stretch",
            ):
                st.session_state.battle_log.append(use_potion())
                st.rerun()

            if a4.button("🏃 도망", width="stretch"):
                st.session_state.battle_log.append("🏃 전투에서 도망쳤습니다.")
                st.session_state.monster = None
                persist()
                st.rerun()

        if st.session_state.battle_log:
            recent_logs = list(reversed(st.session_state.battle_log[-4:]))
            log_html = ''.join(
                f'<div class="combat-log-line">{html.escape(str(log))}</div>'
                for log in recent_logs
            )
            st.markdown(
                '<div class="combat-log">'
                '<div class="combat-log-title">📜 최근 전투 기록</div>'
                f'{log_html}'
                '</div>',
                unsafe_allow_html=True,
            )
            if len(st.session_state.battle_log) > 4:
                with st.expander("전체 전투 기록 보기", expanded=False):
                    for log in reversed(st.session_state.battle_log[-14:]):
                        st.write("• " + str(log))


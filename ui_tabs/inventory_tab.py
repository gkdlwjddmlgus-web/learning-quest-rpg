from game_core import *


def render_inventory_tab() -> None:
    st.markdown(
        '<div class="inventory-head">'
        '<div class="inventory-eyebrow">INVENTORY</div>'
        '<div class="inventory-title">🎒 장비와 아이템</div>'
        '<div class="inventory-copy">장착 장비를 확인하고, 보유 장비를 부위별로 관리하거나 강화할 수 있습니다.</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    equip_view_tab, enhance_view_tab, recycle_view_tab, consumable_view_tab = st.tabs([
        "🛡️ 장비", "⚒️ 강화", "♻️ 분해", "🧪 소모품·포획도구"
    ])

    equipment = [x for x in st.session_state.inventory if x.get("item_type") == "equipment"]

    with equip_view_tab:
        equipped_count = sum(1 for slot in EQUIPMENT_SLOTS if equipped_item(slot))
        total_attack = equipment_attack()
        total_defense = equipment_defense()
        st.markdown(
            f'<div class="inventory-summary">'
            f'<div class="inventory-summary-card"><div class="inventory-summary-label">장착 슬롯</div><div class="inventory-summary-value">{equipped_count} / {len(EQUIPMENT_SLOTS)}</div></div>'
            f'<div class="inventory-summary-card"><div class="inventory-summary-label">장비 공격력</div><div class="inventory-summary-value">⚔️ {total_attack}</div></div>'
            f'<div class="inventory-summary-card"><div class="inventory-summary-label">장비 방어력</div><div class="inventory-summary-value">🛡️ {total_defense}</div></div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        st.markdown("### 장착 슬롯")
        cols = st.columns(5)
        for col, slot in zip(cols, EQUIPMENT_SLOTS):
            with col:
                item = equipped_item(slot)
                if item:
                    slot_name = html.escape(str(item["name"]))
                    slot_meta = f"+{item['enhance_level']} · 공격 {item_attack(item)} · 방어 {item_defense(item)}"
                else:
                    slot_name = "비어 있음"
                    slot_meta = "장비를 선택해 장착하세요"
                st.markdown(
                    f'<div class="equip-slot-card">'
                    f'<div class="equip-slot-label">{SLOT_ICONS[slot]} {html.escape(slot)}</div>'
                    f'<div class="equip-slot-name">{slot_name}</div>'
                    f'<div class="equip-slot-meta">{html.escape(slot_meta)}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
                if item and st.button("해제", key=f"unequip_{slot}", width="stretch"):
                    st.session_state.equipped_items[slot] = None
                    persist()
                    st.rerun()

        st.divider()
        slot_tabs = st.tabs(["전체"] + [f"{SLOT_ICONS[s]} {s}" for s in EQUIPMENT_SLOTS])
        slot_names = [None] + EQUIPMENT_SLOTS

        for slot_tab, slot_name in zip(slot_tabs, slot_names):
            with slot_tab:
                shown = [item for item in equipment if slot_name is None or item.get("slot") == slot_name]
                if not shown:
                    st.info("해당 분류의 장비가 없습니다.")
                else:
                    ordered = sorted(shown, key=lambda x: (EQUIPMENT_SLOTS.index(x['slot']), x['name']))
                    for row_start in range(0, len(ordered), 2):
                        item_cols = st.columns(2)
                        for offset, col in enumerate(item_cols):
                            item_index = row_start + offset
                            if item_index >= len(ordered):
                                continue
                            item = ordered[item_index]
                            with col:
                                is_eq = st.session_state.equipped_items.get(item['slot']) == item['item_id']
                                equipped_text = '<div class="item-equipped">● 현재 장착 중</div>' if is_eq else ''

                                if is_eq:
                                    compare_html = (
                                        '<div class="item-compare">'
                                        '<div class="item-compare-title">현재 장착 기준</div>'
                                        '<div class="item-compare-values"><span class="item-compare-neutral">⚔️ ±0</span><span class="item-compare-neutral">🛡️ ±0</span></div>'
                                        '</div>'
                                    )
                                else:
                                    attack_delta, defense_delta, compare_name = equipment_swap_delta(item)
                                    attack_class = "item-compare-positive" if attack_delta > 0 else "item-compare-negative" if attack_delta < 0 else "item-compare-neutral"
                                    defense_class = "item-compare-positive" if defense_delta > 0 else "item-compare-negative" if defense_delta < 0 else "item-compare-neutral"
                                    compare_html = (
                                        '<div class="item-compare">'
                                        f'<div class="item-compare-title">비교 대상: {html.escape(compare_name)}</div>'
                                        '<div class="item-compare-values">'
                                        f'<span class="{attack_class}">⚔️ {html.escape(format_stat_delta(attack_delta))}</span>'
                                        f'<span class="{defense_class}">🛡️ {html.escape(format_stat_delta(defense_delta))}</span>'
                                        '</div>'
                                        '</div>'
                                    )

                                st.markdown(
                                    f'<div class="item-card">'
                                    f'<div class="item-card-top">'
                                    f'<div class="item-name">{RARITY_ICONS.get(item["rarity"],"⚪")} {html.escape(str(item["name"]))} +{item["enhance_level"]}</div>'
                                    f'<div class="item-badge">{html.escape(str(item["rarity"]))}</div>'
                                    f'</div>'
                                    f'<div class="item-meta">{SLOT_ICONS[item["slot"]]} {html.escape(str(item["slot"]))} · {html.escape(str(item["set_name"]))} 세트 · 보유 {item["quantity"]}개</div>'
                                    f'<div class="item-stats"><span>⚔️ +{item_attack(item)}</span><span>🛡️ +{item_defense(item)}</span></div>'
                                    f'{compare_html}'
                                    f'{equipped_text}'
                                    f'</div>',
                                    unsafe_allow_html=True,
                                )
                                if st.button(
                                    "해제" if is_eq else "장착",
                                    key=f"equip_{slot_name}_{item['item_id']}",
                                    width="stretch",
                                    type="secondary",
                                ):
                                    st.session_state.equipped_items[item['slot']] = None if is_eq else item['item_id']
                                    persist()
                                    st.rerun()

    with enhance_view_tab:
        enhancement_help = (
            "동일 장비 1개를 재료로 강화 1회를 시도합니다. "
            "최대 +15입니다. 성공 확률은 +1~+3 100%, +4 90%부터 +10 30%까지 10%p씩 감소하고, "
            "+11 25%부터 +15 5%까지 5%p씩 감소합니다. "
            "현재 강화 단계가 +10 이하라면 실패해도 단계가 유지되며, 현재 +11 이상에서 실패하면 1단계 하락합니다. "
            "재료는 성공/실패와 관계없이 소모됩니다."
        )
        st.markdown(
            f'<div class="enhance-title-row"><span class="enhance-title-text">⚒️ 장비 강화</span>'
            f'<span class="help-dot" title="{html.escape(enhancement_help, quote=True)}">?</span></div>',
            unsafe_allow_html=True,
        )

        if not equipment:
            st.info("보유 장비가 없습니다.")
        else:
            enhanceable_count = sum(
                1 for item in equipment
                if item.get("quantity", 0) >= 2 and item.get("enhance_level", 0) < MAX_ENHANCE_LEVEL
            )
            st.markdown(
                f'<div class="inventory-summary">'
                f'<div class="inventory-summary-card"><div class="inventory-summary-label">보유 장비 종류</div><div class="inventory-summary-value">{len(equipment)}</div></div>'
                f'<div class="inventory-summary-card"><div class="inventory-summary-label">강화 가능</div><div class="inventory-summary-value">{enhanceable_count}</div></div>'
                f'<div class="inventory-summary-card"><div class="inventory-summary-label">최대 강화</div><div class="inventory-summary-value">+{MAX_ENHANCE_LEVEL}</div></div>'
                f'</div>',
                unsafe_allow_html=True,
            )

            bulk_help = (
                "강화 가능한 모든 장비의 중복 재료를 한 번에 사용합니다. "
                "각 장비는 본체 1개만 남을 때까지 반복 강화되며, +15에 도달하면 즉시 중단됩니다. "
                "모든 시도에는 현재 단계에 맞는 성공 확률과 실패 패널티가 동일하게 적용됩니다."
            )
            st.markdown(
                f'<div class="enhance-subtitle-row"><span class="enhance-subtitle-text">일괄 강화</span>'
                f'<span class="help-dot" title="{html.escape(bulk_help, quote=True)}">?</span></div>',
                unsafe_allow_html=True,
            )

            if st.button(
                f"⚒️ 일괄 강화 · {enhanceable_count}종",
                key="enhance_all_materials",
                disabled=enhanceable_count <= 0,
                width="stretch",
                type="primary",
            ):
                total_attempts = 0
                total_successes = 0
                total_failures = 0
                total_downgrades = 0
                item_results: list[str] = []

                for bulk_item in equipment:
                    if bulk_item.get("quantity", 0) < 2 or bulk_item.get("enhance_level", 0) >= MAX_ENHANCE_LEVEL:
                        continue

                    item_attempts = 0
                    item_successes = 0
                    item_failures = 0
                    item_downgrades = 0
                    start_level = int(bulk_item.get("enhance_level", 0))
                    start_quantity = int(bulk_item.get("quantity", 0))

                    while (
                        int(bulk_item.get("quantity", 0)) >= 2
                        and int(bulk_item.get("enhance_level", 0)) < MAX_ENHANCE_LEVEL
                    ):
                        success, before, after, rate = attempt_equipment_enhancement(bulk_item)
                        item_attempts += 1
                        total_attempts += 1
                        if success:
                            item_successes += 1
                            total_successes += 1
                        else:
                            item_failures += 1
                            total_failures += 1
                            if after < before:
                                item_downgrades += 1
                                total_downgrades += 1

                    end_level = int(bulk_item.get("enhance_level", 0))
                    consumed = start_quantity - int(bulk_item.get("quantity", 0))
                    item_results.append(
                        f"{bulk_item['name']} +{start_level}→+{end_level} "
                        f"(재료 {consumed}개 · 성공 {item_successes} · 실패 {item_failures}"
                        + (f" · 하락 {item_downgrades}" if item_downgrades else "")
                        + ")"
                    )

                if total_attempts:
                    st.session_state.inventory_message = (
                        f"일괄 강화 완료 · 총 {total_attempts}회 시도 · "
                        f"성공 {total_successes} · 실패 {total_failures}"
                        + (f" · 단계 하락 {total_downgrades}" if total_downgrades else "")
                    )
                    if item_results:
                        st.session_state.inventory_message += " | " + " / ".join(item_results)
                    persist()
                    st.rerun()

            ordered = sorted(equipment, key=lambda x: (EQUIPMENT_SLOTS.index(x['slot']), x['name']))
            for row_start in range(0, len(ordered), 2):
                enhance_cols = st.columns(2)
                for offset, col in enumerate(enhance_cols):
                    item_index = row_start + offset
                    if item_index >= len(ordered):
                        continue
                    item = ordered[item_index]
                    with col:
                        current_level = int(item.get('enhance_level', 0))
                        can = item['quantity'] >= 2 and current_level < MAX_ENHANCE_LEVEL
                        if current_level < MAX_ENHANCE_LEVEL:
                            target_level = current_level + 1
                            success_rate = enhancement_success_rate(target_level)
                            preview = dict(item)
                            preview['enhance_level'] = target_level
                            failure_text = (
                                f"실패 시 +{max(0, current_level - 1)}로 하락"
                                if enhancement_failure_drops(current_level)
                                else f"실패 시 +{current_level} 유지"
                            )
                            item_help = (
                                f"다음 강화: +{target_level}\n"
                                f"성공 확률: {success_rate:.0%}\n"
                                f"성공 시: 공격 {item_attack(preview)} / 방어 {item_defense(preview)}\n"
                                f"{failure_text}\n"
                                "재료: 동일 장비 1개"
                            )
                        else:
                            target_level = current_level
                            success_rate = 0.0
                            item_help = "최대 강화 +15에 도달한 장비입니다."

                        st.markdown(
                            f'<div class="enhance-card">'
                            f'<div class="item-card-top"><div class="item-name">{SLOT_ICONS[item["slot"]]} {RARITY_ICONS.get(item["rarity"],"⚪")} {html.escape(str(item["name"]))} +{current_level} '
                            f'<span class="help-dot" title="{html.escape(item_help, quote=True)}">?</span></div><div class="item-badge">보유 {item["quantity"]}</div></div>'
                            f'<div class="item-meta">{html.escape(str(item["rarity"]))} · {html.escape(str(item["set_name"]))} 세트</div>'
                            f'<div class="item-stats"><span>⚔️ {item_attack(item)}</span><span>🛡️ {item_defense(item)}</span></div>'
                            f'</div>',
                            unsafe_allow_html=True,
                        )
                        button_label = (
                            f"⚒️ +{target_level} 강화 시도 · {success_rate:.0%}"
                            if can
                            else ("MAX" if current_level >= MAX_ENHANCE_LEVEL else "재료 부족")
                        )
                        if st.button(
                            button_label,
                            key=f"enhance_allview_{item['item_id']}",
                            disabled=not can,
                            width="stretch",
                        ):
                            success, before, after, rate = attempt_equipment_enhancement(item)
                            if success:
                                st.session_state.inventory_message = (
                                    f"✨ {item['name']} 강화 성공! +{before} → +{after} (성공 확률 {rate:.0%})"
                                )
                            elif after < before:
                                st.session_state.inventory_message = (
                                    f"💥 {item['name']} 강화 실패 · +{before} → +{after} 하락 (성공 확률 {rate:.0%})"
                                )
                            else:
                                st.session_state.inventory_message = (
                                    f"⚠️ {item['name']} 강화 실패 · +{before} 유지 (성공 확률 {rate:.0%})"
                                )
                            persist()
                            st.rerun()

    with recycle_view_tab:
        st.markdown("### ♻️ 장비 분해")
        st.caption("사용하지 않는 장비를 강화 파편으로 바꿉니다. 장착 중인 장비는 분해할 수 없습니다.")
        st.metric("보유 강화 파편", int(st.session_state.extra.get("dismantle_shards", 0)))

        recyclable = [
            item for item in equipment
            if st.session_state.equipped_items.get(item.get("slot")) != item.get("item_id")
            and int(item.get("quantity", 0)) > 0
        ]
        if not recyclable:
            st.info("분해 가능한 장비가 없습니다.")
        else:
            for row_start in range(0, len(recyclable), 2):
                cols = st.columns(2)
                for offset, col in enumerate(cols):
                    idx = row_start + offset
                    if idx >= len(recyclable):
                        continue
                    item = recyclable[idx]
                    with col:
                        reward = dismantle_reward(item)
                        st.markdown(
                            f'<div class="item-card"><div class="item-card-top">'
                            f'<div class="item-name">{RARITY_ICONS.get(item.get("rarity"), "⚪")} {html.escape(str(item.get("name")))} +{int(item.get("enhance_level",0))}</div>'
                            f'<div class="item-badge">보유 {int(item.get("quantity",0))}</div></div>'
                            f'<div class="item-meta">1개 분해 시 강화 파편 +{reward}</div>'
                            f'<div class="item-stats"><span>⚔️ +{item_attack(item)}</span><span>🛡️ +{item_defense(item)}</span></div></div>',
                            unsafe_allow_html=True,
                        )
                        max_qty = int(item.get("quantity", 0))
                        qty = st.number_input("분해 수량", min_value=1, max_value=max_qty, value=1, step=1, key=f"dismantle_qty_{item['item_id']}")
                        if st.button(f"♻️ 분해 · 파편 +{reward * int(qty)}", key=f"dismantle_{item['item_id']}", width="stretch"):
                            ok, msg = dismantle_equipment(item["item_id"], int(qty))
                            st.session_state.inventory_message = msg
                            st.rerun()

    with consumable_view_tab:
        st.markdown("### 🧪 소모품")
        potion_col, spacer_col = st.columns([1, 2])
        with potion_col:
            st.markdown(
                f'<div class="consumable-card"><div class="consumable-name">🧪 회복 물약</div><div class="consumable-count">{potion_count()}개</div><div class="consumable-meta">최대 HP의 {int(POTION_HEAL_RATE * 100)}% 회복</div></div>',
                unsafe_allow_html=True,
            )
            if st.button(
                "물약 사용",
                disabled=potion_count() <= 0 or st.session_state.player_hp >= max_hp(),
                width="stretch",
            ):
                st.session_state.event_message = use_potion()
                st.rerun()

        st.divider()
        st.markdown("### 🎯 포획 도구")
        ball_cols = st.columns(3)
        for col, ball_id in zip(ball_cols, CAPTURE_ITEMS):
            with col:
                ball = CAPTURE_ITEMS[ball_id]
                bonus_text = "기본 포획률" if ball['bonus'] <= 0 else f"포획률 +{ball['bonus']:.0%}"
                st.markdown(
                    f'<div class="consumable-card">'
                    f'<div class="consumable-name">{ball["icon"]} {html.escape(str(ball["name"]))}</div>'
                    f'<div class="consumable-count">{capture_item_count(ball_id)}개</div>'
                    f'<div class="consumable-meta">{html.escape(bonus_text)}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

    if st.session_state.inventory_message:
        st.success(st.session_state.inventory_message)


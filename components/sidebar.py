from game_core import *
from auth import logout


def render_sidebar() -> None:
    with st.sidebar:
        active_world_sidebar = get_active_learning_world()
        level = int(st.session_state.level)
        xp_now = int(st.session_state.xp)
        xp_need = max(1, required_xp(level))
        xp_ratio = min(max(xp_now / xp_need, 0.0), 1.0)
        hp_now = max(0, int(st.session_state.player_hp))
        hp_max = max(1, max_hp())
        hp_ratio = min(max(hp_now / hp_max, 0.0), 1.0)

        selected_title = html.escape(str(st.session_state.extra.get("selected_title", "초보 분석가")))
        job_name = html.escape(str(st.session_state.extra.get("job", "미전직")))

        hud_html = f"""<div class="hud-card">
    <div class="hud-eyebrow">PLAYER STATUS</div>
    <div class="hud-title">🧙 {selected_title}</div>
    <div class="hud-subtitle">{job_name}</div>
    <div class="hud-level-row">
    <div class="hud-level">LV.{level}</div>
    <div class="hud-xp">XP {xp_now:,} / {xp_need:,}</div>
    </div>
    <div class="hud-bar"><div class="hud-bar-fill" style="width:{xp_ratio * 100:.1f}%"></div></div>
    <div class="hud-hp-row">
    <span>❤️ HP</span><span class="hud-hp-value">{hp_now} / {hp_max}</span>
    </div>
    <div class="hud-hp-bar"><div class="hud-hp-fill" style="width:{hp_ratio * 100:.1f}%"></div></div>
    <div class="hud-grid">
    <div class="hud-stat"><div class="hud-stat-label">⚔️ ATTACK</div><div class="hud-stat-value">{player_attack()}</div></div>
    <div class="hud-stat"><div class="hud-stat-label">🛡️ DEFENSE</div><div class="hud-stat-value">{player_defense()}</div></div>
    </div>
    <div class="hud-resource-grid">
    <div class="hud-resource"><div class="hud-resource-value">🎫 {st.session_state.battle_tickets}</div><div class="hud-resource-label">전투권</div></div>
    <div class="hud-resource"><div class="hud-resource-value">🧪 {potion_count()}</div><div class="hud-resource-label">물약</div></div>
    <div class="hud-resource"><div class="hud-resource-value">🔥 {st.session_state.extra.get('streak', 0)}</div><div class="hud-resource-label">연속 학습</div></div>
    </div>
    </div>"""
        st.markdown(hud_html, unsafe_allow_html=True)

        st.markdown('<div class="hud-section-title">CURRENT WORLD</div>', unsafe_allow_html=True)
        if active_world_sidebar:
            world_name = html.escape(str(active_world_sidebar.get("world_name", "이름 없는 월드")))
            world_topic = html.escape(str(active_world_sidebar.get("topic", "")))
            st.markdown(
                f"""
                <div class="hud-world">
                    <div class="hud-world-name">🌍 {world_name}</div>
                    <div class="hud-world-topic">{world_topic}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.caption("아직 생성된 학습 월드가 없습니다.")

        st.markdown('<div class="hud-section-title">ATTRIBUTES</div>', unsafe_allow_html=True)
        st.markdown(
            f"""
            <div class="hud-stat-grid">
                <div class="hud-mini-stat"><span>INT</span><b>{st.session_state.intelligence}</b></div>
                <div class="hud-mini-stat"><span>WIS</span><b>{st.session_state.wisdom}</b></div>
                <div class="hud-mini-stat"><span>VIT</span><b>{st.session_state.vitality}</b></div>
                <div class="hud-mini-stat"><span>LUK</span><b>{st.session_state.luck}</b></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.session_state.stat_points > 0:
            st.caption(f"사용 가능한 스탯 포인트: {st.session_state.stat_points}")
            stat = st.selectbox("올릴 스탯", ["INT", "WIS", "VIT", "LUK"])
            if st.button("스탯 +1", width="stretch"):
                key = {"INT": "intelligence", "WIS": "wisdom", "VIT": "vitality", "LUK": "luck"}[stat]
                st.session_state[key] += 1
                st.session_state.stat_points -= 1
                if stat == "VIT":
                    st.session_state.player_hp = max_hp()
                persist()
                st.rerun()

        st.markdown('<div class="hud-section-title">ACTIONS</div>', unsafe_allow_html=True)
        for skill, info in SKILLS.items():
            used = st.session_state.extra["skill_uses"].get(skill, 0)
            remaining = max(0, int(info["daily_limit"]) - int(used))
            display_name = str(info.get("display_name", skill))
            icon = str(info.get("icon", "✨"))

            action_col, help_col = st.columns([6.5, 1], gap="small")
            with action_col:
                if st.button(
                    f"{icon} {display_name}  ·  {remaining}회 남음",
                    key=f"skill_{skill}",
                    width="stretch",
                ):
                    st.session_state.event_message = use_skill(skill)
                    st.rerun()

            with help_col:
                help_text = (
                    f"{icon} {display_name}\n\n"
                    f"{info.get('description', '')}\n\n"
                    f"효과: {info.get('effect', '')}\n\n"
                    f"하루 {int(info['daily_limit'])}회 사용 가능"
                )
                # st.button의 help 툴팁을 사용해 작은 '?'만 표시한다.
                # popover가 아니므로 Streamlit 기본 화살표가 붙지 않는다.
                st.button(
                    "?",
                    key=f"skill_help_{skill}",
                    help=help_text,
                    width="stretch",
                )
        st.markdown('<div class="hud-section-title">ACCOUNT</div>', unsafe_allow_html=True)
        st.caption(
            f"{st.session_state.get('auth_display_name', '사용자')} · "
            f"{st.session_state.get('auth_test_tier', '')}"
        )
        if st.button("🚪 로그아웃", key="logout_button", width="stretch"):
            logout()


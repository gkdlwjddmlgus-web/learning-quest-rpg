import streamlit as st

st.set_page_config(
    page_title="Learning Quest RPG",
    page_icon="⚔️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 첫 로그인 화면부터 sidebar DOM을 만들어 둔다.
# 로그인 후 실제 HUD가 렌더링될 때 이 placeholder는 제거된다.
_sidebar_bootstrap = st.sidebar.empty()

from components.styles import inject_styles
inject_styles()

from auth import login_gate

if not login_gate():
    st.stop()

import game_core as core
core.initialize_player_session()
core.initialize_temp_session()
core.seed_test_profile_if_needed()
core.refresh_daily_state()

from onboarding.world_gate import render_world_gate

if not render_world_gate():
    st.stop()

from components.sidebar import render_sidebar
from world_ui.village_hub import render_village_hub
from ui_tabs.world_tab import render_world_tab
from ui_tabs.quest_tab import render_quest_tab
from ui_tabs.battle_tab import render_battle_tab
from ui_tabs.inventory_tab import render_inventory_tab
from ui_tabs.monster_tab import render_monster_tab
from ui_tabs.daily_tab import render_daily_tab
from ui_tabs.wrong_tab import render_wrong_tab
from ui_tabs.record_tab import render_record_tab
from ui_tabs.profile_tab import render_profile_tab

_sidebar_bootstrap.empty()
render_sidebar()

if "game_view" not in st.session_state:
    st.session_state.game_view = "hub"

view = st.session_state.game_view

ROUTES = {
    "world": ("🌍 학습 월드", render_world_tab),
    "quest": ("🗼 성장의 탑", render_quest_tab),
    "battle": ("⚔️ 사냥터 · 던전", render_battle_tab),
    "inventory": ("⚒️ 장비 공방", render_inventory_tab),
    "monster": ("🐲 몬스터 연구소", render_monster_tab),
    "daily": ("🏛️ 모험가 길드", render_daily_tab),
    "wrong": ("📚 기억의 도서관", render_wrong_tab),
    "record": ("🔭 관측소", render_record_tab),
    "profile": ("⚔️ 전직관 · 성장", render_profile_tab),
}

if view == "hub":
    render_village_hub()
else:
    label, renderer = ROUTES.get(view, ROUTES["world"])

    top_left, top_right, top_logout = st.columns([1, 3.6, 1])
    if top_left.button("← 마을로", key="return_to_village", width="stretch"):
        st.session_state.game_view = "hub"
        st.rerun()

    if top_logout.button("🚪 로그아웃", key="location_logout", width="stretch"):
        from auth import logout
        logout()

    origin = str(st.session_state.get("game_view_origin", "")).strip()
    with top_right:
        st.markdown(
            f"""
            <div class="location-route-head">
              <div class="location-route-kicker">CURRENT LOCATION</div>
              <div class="location-route-title">{label}</div>
              <div class="location-route-copy">{origin + '에서 진입했습니다.' if origin else '마을에서 진입한 기능 공간입니다.'}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    renderer()

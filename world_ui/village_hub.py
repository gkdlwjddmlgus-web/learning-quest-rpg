from __future__ import annotations

import base64
import html
import textwrap
from dataclasses import dataclass
from pathlib import Path

import streamlit as st

import core
from core import get_active_learning_world, get_learning_worlds, set_active_learning_world


PROJECT_ROOT = Path(__file__).resolve().parent.parent
ASSET_ROOT = PROJECT_ROOT / "assets"

THEME_KEYS = {
    "판타지": "fantasy",
    "무협": "murim",
    "SF": "sf",
    "귀여운 몬스터": "cute",
    "다크 판타지": "dark_fantasy",
    "현대": "modern",
}

AVATARS = {
    "explorer": "탐험가",
    "warrior": "검사",
    "mage": "마도사",
    "scholar": "학자",
    "ranger": "정찰자",
    "monk": "수련가",
}


@dataclass(frozen=True)
class Place:
    key: str
    icon: str
    name: str
    route: str
    section: str
    tagline: str
    description: str


THEME_NAMES = {
    "판타지": {
        "tower": ("🗼", "성장의 탑"), "guild": ("🏛️", "모험가 길드"),
        "hunt": ("🌲", "사냥터"), "dungeon": ("🏰", "던전 게이트"),
        "forge": ("⚒️", "장비 공방"), "bestiary": ("🐲", "몬스터 연구소"),
        "library": ("📚", "기억의 도서관"), "observatory": ("🔭", "관측소"),
        "classhall": ("⚔️", "전직관"), "world": ("🌍", "세계 기록실"),
    },
    "무협": {
        "tower": ("🗼", "무공탑"), "guild": ("🏮", "객잔 의뢰소"),
        "hunt": ("🎋", "수련림"), "dungeon": ("⛰️", "비경 입구"),
        "forge": ("⚒️", "대장간"), "bestiary": ("🐉", "영수원"),
        "library": ("📜", "기억서고"), "observatory": ("☯️", "천기각"),
        "classhall": ("🥋", "전직관"), "world": ("🗺️", "강호지"),
    },
    "SF": {
        "tower": ("🗼", "성장 코어 타워"), "guild": ("🛰️", "중앙 의뢰국"),
        "hunt": ("🌌", "외곽 탐사구역"), "dungeon": ("🚪", "심층 게이트"),
        "forge": ("🛠️", "장비 랩"), "bestiary": ("🤖", "생명체 분석실"),
        "library": ("💾", "기억 아카이브"), "observatory": ("📡", "데이터 관측소"),
        "classhall": ("🧬", "클래스 연구소"), "world": ("🪐", "월드 아카이브"),
    },
    "귀여운 몬스터": {
        "tower": ("🏰", "성장의 별탑"), "guild": ("🎪", "모험 친구 광장"),
        "hunt": ("🌼", "초원길"), "dungeon": ("🍭", "비밀 동굴"),
        "forge": ("🧰", "반짝 공방"), "bestiary": ("🐾", "몬스터 놀이터"),
        "library": ("📚", "기억 책방"), "observatory": ("🔭", "별빛 관측소"),
        "classhall": ("🎓", "꿈꾸는 전직소"), "world": ("🌈", "세계 앨범"),
    },
    "다크 판타지": {
        "tower": ("🗼", "심연의 탑"), "guild": ("🕯️", "검은 계약소"),
        "hunt": ("🌑", "잿빛 황야"), "dungeon": ("🚪", "심연문"),
        "forge": ("⚒️", "흑철 공방"), "bestiary": ("🐺", "마수 연구실"),
        "library": ("📕", "망각의 서고"), "observatory": ("🔮", "예언 관측소"),
        "classhall": ("🗡️", "각성의 전당"), "world": ("🕸️", "금서 기록실"),
    },
    "현대": {
        "tower": ("🏙️", "성장 타워"), "guild": ("🏢", "의뢰 센터"),
        "hunt": ("🛣️", "실전 훈련장"), "dungeon": ("🏢", "심화 훈련동"),
        "forge": ("🛠️", "장비 작업실"), "bestiary": ("🧪", "몬스터 연구실"),
        "library": ("📚", "기억 도서관"), "observatory": ("📊", "분석 센터"),
        "classhall": ("🎓", "커리어 센터"), "world": ("🌐", "월드 센터"),
    },
}

PLACE_META = {
    "tower": ("퀘스트", "다음 성장을 위한 학습 퀘스트", "문제를 풀고 경험치와 전투권을 획득합니다."),
    "guild": ("일일 퀘스트", "오늘의 의뢰를 확인하는 곳", "오늘 수행할 반복 학습 목표와 일일 의뢰를 확인합니다."),
    "hunt": ("일반 사냥", "가볍게 전투를 시작하는 지역", "일반 몬스터를 상대하며 경험치·장비·포획 기회를 얻습니다."),
    "dungeon": ("던전 / 보스", "강한 적이 기다리는 심화 전투", "강한 적과 보스에게 도전하고 학습 전투 기믹을 경험합니다."),
    "forge": ("인벤토리", "장비 관리와 전투 준비", "장비를 장착·강화·분해하고 전투 준비를 합니다."),
    "bestiary": ("몬스터", "동료 몬스터 관리", "포획한 몬스터 도감과 팀 편성을 확인합니다."),
    "library": ("오답 던전", "실수를 성장으로 바꾸는 장소", "틀린 문제를 다시 풀어 약점을 보완합니다."),
    "observatory": ("학습 기록", "학습 데이터를 관측하는 곳", "학습량·정답률·분야별 기록을 확인합니다."),
    "classhall": ("성장", "플레이어 성장과 전직", "능력치와 성장 상태를 확인하고 전직을 준비합니다."),
    "world": ("학습 월드", "현재 세계의 전체 기록", "학습 영역·지역·몬스터와 월드 정보를 확인합니다."),
}

ROUTES = [
    ("guild", "daily"),
    ("tower", "quest"),
    ("hunt", "battle"),
    ("dungeon", "battle"),
    ("forge", "inventory"),
    ("bestiary", "monster"),
    ("library", "wrong"),
    ("observatory", "record"),
    ("classhall", "profile"),
    ("world", "world"),
]


def _safe_html(markup: str) -> str:
    """Streamlit Markdown이 들여쓰기된 HTML을 코드블록으로 오해하지 않도록 한 줄로 정규화한다."""
    return " ".join(line.strip() for line in str(markup).splitlines() if line.strip())


def _places(theme: str) -> list[Place]:
    names = THEME_NAMES.get(theme, THEME_NAMES["판타지"])
    result = []
    for key, route in ROUTES:
        section, tagline, description = PLACE_META[key]
        icon, name = names[key]
        result.append(Place(key, icon, name, route, section, tagline, description))
    return result


def _data_uri(path: Path) -> str:
    if not path.exists():
        return ""
    mime = {
        ".svg": "image/svg+xml", ".png": "image/png", ".webp": "image/webp",
        ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
    }.get(path.suffix.lower(), "application/octet-stream")
    return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode('ascii')}"


def _theme_asset(theme: str, name: str) -> str:
    folder = ASSET_ROOT / "themes" / THEME_KEYS.get(theme, "fantasy")
    for ext in (".webp", ".png", ".jpg", ".jpeg", ".svg"):
        path = folder / f"{name}{ext}"
        if path.exists():
            return _data_uri(path)
    return ""


def _avatar_asset(avatar_id: str) -> str:
    for ext in (".webp", ".png", ".jpg", ".jpeg", ".svg"):
        path = ASSET_ROOT / "avatars" / f"{avatar_id}{ext}"
        if path.exists():
            return _data_uri(path)
    return ""


def _current_avatar_id() -> str:
    avatar_id = str(st.session_state.get("extra", {}).get("avatar_id", "explorer"))
    return avatar_id if avatar_id in AVATARS else "explorer"


def _save_avatar(avatar_id: str) -> None:
    st.session_state.setdefault("extra", {})["avatar_id"] = avatar_id
    if hasattr(core, "persist"):
        try:
            core.persist()
        except Exception:
            pass


def _carousel_key(world_id: int, size: int) -> str:
    key = f"hub_carousel_index_{world_id}"
    st.session_state[key] = int(st.session_state.get(key, 0)) % size
    return key


def _shift(key: str, delta: int, size: int) -> None:
    st.session_state[key] = (int(st.session_state.get(key, 0)) + delta) % size


def _keyboard_bridge() -> None:
    """허브 전용 정확한 버튼명만 클릭한다. Deploy 버튼은 절대 탐색하지 않는다."""
    st.iframe(
        """
<script>
(() => {
  try {
    const doc = window.parent.document;
    const marker = "__learningQuestHubV7Keys";
    if (window.parent[marker]) doc.removeEventListener("keydown", window.parent[marker], true);

    const txt = (el) => (el?.innerText || "").replace(/\\s+/g, " ").trim();
    const isTyping = (el) => {
      const tag = (el?.tagName || "").toLowerCase();
      return ["input","textarea","select"].includes(tag) || !!el?.isContentEditable;
    };
    const clickExact = (label) => {
      const button = [...doc.querySelectorAll("button")]
        .find(b => txt(b) === label && !b.disabled);
      if (!button) return false;
      button.click();
      return true;
    };
    const clickEnter = () => {
      const button = [...doc.querySelectorAll("button")]
        .find(b => txt(b).startsWith("E · ") && txt(b).endsWith(" 입장") && !b.disabled);
      if (!button) return false;
      button.click();
      return true;
    };

    const handler = (event) => {
      if (isTyping(event.target)) return;
      const key = (event.key || "").toLowerCase();
      let handled = false;
      if (key === "a" || key === "arrowleft") handled = clickExact("◀ 이전 장소");
      else if (key === "d" || key === "arrowright") handled = clickExact("다음 장소 ▶");
      else if (key === "e" || key === "enter") handled = clickEnter();

      if (handled) {
        event.preventDefault();
        event.stopPropagation();
      }
    };

    window.parent[marker] = handler;
    doc.addEventListener("keydown", handler, true);
  } catch (err) {
    console.warn("Hub keyboard bridge unavailable:", err);
  }
})();
</script>
        """,
        width=1,
        height=1,
        tab_index=-1,
    )


def _signed_offset(index: int, active: int, count: int) -> int:
    value = (index - active) % count
    return value - count if value > count // 2 else value


def _carousel_html(places: list[Place], active: int, theme: str, world_name: str) -> str:
    slot_class = {-2: "far-left", -1: "left", 0: "active", 1: "right", 2: "far-right"}
    cards: list[str] = []

    for index, place in enumerate(places):
        offset = _signed_offset(index, active, len(places))
        if offset not in slot_class:
            continue

        art_uri = _theme_asset(theme, place.key)
        art = (
            f'<img class="hub6-art" src="{art_uri}" alt="{html.escape(place.name)}">'
            if art_uri
            else f'<div class="hub6-fallback">{html.escape(place.icon)}</div>'
        )

        # 선택 카드에는 상세 설명까지, 뒤쪽 카드에는 이름/분류만 보여준다.
        detail = (
            f'<div class="hub6-description">{html.escape(place.description)}</div>'
            if offset == 0 else ""
        )

        cards.append(
            f'<div class="hub6-card {slot_class[offset]}">'
            f'<div class="hub6-art-wrap">{art}</div>'
            f'<div class="hub6-card-body">'
            f'<div class="hub6-section">{html.escape(place.section)}</div>'
            f'<div class="hub6-name">{html.escape(place.name)}</div>'
            f'<div class="hub6-tagline">{html.escape(place.tagline)}</div>'
            f'{detail}'
            f'</div></div>'
        )

    background = _theme_asset(theme, "background")
    bg_style = (
        f"background-image:linear-gradient(rgba(2,18,29,.22),rgba(2,18,29,.62)),url('{background}');"
        if background else ""
    )

    theme_class = f"theme-{THEME_KEYS.get(theme, 'fantasy')}"

    return (
        f'<div class="hub6-shell {theme_class}" style="{bg_style}">'
        f'<div class="hub6-world-kicker">WORLD HUB · {html.escape(theme)}</div>'
        f'<div class="hub6-world-name">{html.escape(world_name)}</div>'
        f'<div class="hub6-stage">{"".join(cards)}</div>'
        f'<div class="hub6-hint">'
        f'<span class="hub6-hint-key">A / ←</span> 이전'
        f'<span class="hub6-hint-sep">·</span>'
        f'<span class="hub6-hint-key">D / →</span> 다음'
        f'<span class="hub6-hint-sep">·</span>'
        f'<span class="hub6-hint-key">E / Enter</span> 입장'
        f'</div>'
        f'</div>'
    )

def _render_world_switcher(active_world: dict) -> None:
    worlds = get_learning_worlds()
    if not worlds:
        return

    open_key = "hub_world_switch_open"
    current_id = int(active_world["id"])

    left, change_col, new_col = st.columns([3.8, 1.1, 1.1])
    with left:
        st.markdown(
            _safe_html(textwrap.dedent(f"""
            <div class="hub6-world-current">
              <div class="hub6-world-current-kicker">CURRENT WORLD</div>
              <div class="hub6-world-current-name">🌍 {html.escape(str(active_world.get("world_name", "이름 없는 세계")))}</div>
              <div class="hub6-world-current-meta">{html.escape(str(active_world.get("topic", "")))}</div>
            </div>
            """).strip()),
            unsafe_allow_html=True,
        )

    with change_col:
        label = "닫기" if st.session_state.get(open_key, False) else "🌍 월드 변경"
        if st.button(label, key="hub_world_switch_toggle", width="stretch"):
            st.session_state[open_key] = not st.session_state.get(open_key, False)
            st.rerun()

    with new_col:
        if st.button("＋ 새 월드", key="hub_new_world", width="stretch"):
            from onboarding.world_gate import open_world_gate
            open_world_gate("create")

    if not st.session_state.get(open_key, False):
        return

    with st.container(border=True):
        world_ids = [int(w["id"]) for w in worlds]
        selected_id = st.selectbox(
            "보유 월드",
            world_ids,
            index=world_ids.index(current_id) if current_id in world_ids else 0,
            format_func=lambda wid: next(
                f"{w.get('world_name', '이름 없는 세계')} · {w.get('topic', '')}"
                for w in worlds if int(w["id"]) == int(wid)
            ),
            key="hub_world_switch_select",
        )
        selected = next(w for w in worlds if int(w["id"]) == int(selected_id))
        st.caption(f"🎯 {selected.get('goal', '학습 목표 없음')} · 🎨 {selected.get('game_theme', '판타지')}")

        c1, c2 = st.columns([2.2, 1])
        if c1.button(
            "이 월드로 이동",
            key="hub_world_switch_confirm",
            type="primary",
            width="stretch",
            disabled=int(selected_id) == current_id,
        ):
            if set_active_learning_world(int(selected_id)):
                st.session_state[open_key] = False
                st.session_state.game_view = "hub"
                st.rerun()
            st.error("월드 변경에 실패했습니다.")

        if c2.button("취소", key="hub_world_switch_cancel", width="stretch"):
            st.session_state[open_key] = False
            st.rerun()


def _render_avatar_selector() -> None:
    current = _current_avatar_id()
    with st.expander("🧙 캐릭터 외형 설정", expanded=False):
        ids = list(AVATARS)
        selected = st.selectbox(
            "아바타 프리셋",
            ids,
            index=ids.index(current),
            format_func=lambda avatar_id: AVATARS[avatar_id],
            key="hub_avatar_selector",
        )
        preview, action = st.columns([1, 2])
        with preview:
            uri = _avatar_asset(selected)
            if uri:
                st.image(uri, width=90)
        with action:
            st.caption("향후 실제 PNG/WebP 캐릭터 이미지로 교체 가능한 프리셋 구조입니다.")
            if selected != current and st.button("이 외형 사용", type="primary", width="stretch"):
                _save_avatar(selected)
                st.rerun()


def render_village_hub() -> None:
    world = get_active_learning_world()
    if not world:
        st.warning("활성 학습 월드가 없습니다. 세계의 문에서 월드를 먼저 선택하세요.")
        return

    world_id = int(world["id"])
    theme = str(world.get("game_theme") or world.get("theme") or "판타지")
    world_name = str(world.get("world_name") or "이름 없는 세계")
    places = _places(theme)

    key = _carousel_key(world_id, len(places))
    active = int(st.session_state[key])
    selected = places[active]

    st.markdown(_safe_html('<div class="hub6-mode-marker"></div>'), unsafe_allow_html=True)
    _keyboard_bridge()

    account, logout_col = st.columns([5, 1])
    with account:
        display_name = html.escape(str(st.session_state.get("auth_display_name", "플레이어")))
        tier = html.escape(str(st.session_state.get("auth_test_tier", "")))
        st.markdown(
            _safe_html(
                f'<div class="hub6-account"><span class="hub6-dot"></span><b>{display_name}</b><span>{tier}</span>'
                f'<span class="hub6-key-help">A/D · ←/→ 장소 선택 · E/Enter 입장</span></div>'
            ),
            unsafe_allow_html=True,
        )
    with logout_col:
        if st.button("🚪 로그아웃", key="hub_logout", width="stretch"):
            from auth import logout
            logout()

    _render_world_switcher(world)

    # strip/dedent된 HTML만 전달하여 Markdown 코드블록으로 해석되지 않게 한다.
    st.markdown(
        _safe_html(_carousel_html(places, active, theme, world_name)),
        unsafe_allow_html=True,
    )

    prev_col, enter_col, next_col = st.columns([1, 1.55, 1])
    if prev_col.button("◀ 이전 장소", key="hub6_prev", width="stretch"):
        _shift(key, -1, len(places))
        st.rerun()

    if enter_col.button(
        f"E · {selected.name} 입장",
        key="hub6_enter",
        type="primary",
        width="stretch",
    ):
        st.session_state.game_view = selected.route
        st.session_state.game_view_origin = selected.name
        st.rerun()

    if next_col.button("다음 장소 ▶", key="hub6_next", width="stretch"):
        _shift(key, 1, len(places))
        st.rerun()

    lower_left, lower_right = st.columns([2.3, 1], gap="large")
    with lower_left:
        st.markdown(
            _safe_html(
                '<div class="hub6-help"><b>월드 허브</b><br>'
                '장소 카드를 넘기며 설명을 확인하고 필요한 기능으로 바로 진입합니다.</div>'
            ),
            unsafe_allow_html=True,
        )
    with lower_right:
        _render_avatar_selector()

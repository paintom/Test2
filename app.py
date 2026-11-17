"""쇼핑 리스트 앱 (2단계: 주요 기능 구현)

PRD 필수 기능 F1~F4, 선택 기능 F5~F7을 구현한다.
상태 변경은 모두 콜백에서 처리하고, 위젯 key는 항목 id 기반으로 만든다.
"""

import re
import uuid

import streamlit as st

st.set_page_config(page_title="쇼핑 리스트", page_icon="🛒")


# ---- 상태 / 모델 ----

def new_item(name: str) -> dict:
    """아이템 데이터 모델: {id, name, checked}"""
    return {"id": str(uuid.uuid4()), "name": name, "checked": False}


def init_state() -> None:
    """session_state 초기화"""
    st.session_state.setdefault("items", [])  # list[dict]
    st.session_state.setdefault("editing_id", None)  # 수정 중인 항목 id
    st.session_state.setdefault("flash", None)  # 콜백에서 남기는 안내 메시지


def find_item(item_id: str) -> dict | None:
    for item in st.session_state["items"]:
        if item["id"] == item_id:
            return item
    return None


def escape_md(text: str) -> str:
    """사용자 입력이 마크다운으로 해석되지 않도록 이스케이프

    콜론은 백슬래시 대신 HTML 엔티티(&#58;)로 바꾼다. `\\:`는 :material/xxx: 같은
    아이콘 단축 표기를 막지 못하기 때문이다.
    """
    escaped = re.sub(r"([\\`*_{}\[\]()#+\-.!|~<>$&])", r"\\\1", text)
    return escaped.replace(":", "&#58;")


def drop_widget_keys(item_id: str) -> None:
    """삭제된 항목의 위젯 상태 제거"""
    for prefix in ("chk_", "edit_"):
        st.session_state.pop(f"{prefix}{item_id}", None)


# ---- 기능 함수 (콜백) ----

def add_item() -> None:
    """F1: 아이템 추가. 입력값은 폼 위젯(new_name)에서 읽는다."""
    name = st.session_state.get("new_name", "").strip()
    if not name:
        st.session_state["flash"] = "아이템 이름을 입력해주세요."
        return
    st.session_state["items"].append(new_item(name))


def start_edit(item_id: str) -> None:
    """F2: 수정 모드 진입 (한 번에 한 항목만)"""
    old_id = st.session_state["editing_id"]
    if old_id and old_id != item_id:
        st.session_state.pop(f"edit_{old_id}", None)
    st.session_state.pop("edit_flash", None)
    item = find_item(item_id)
    if item is None:
        return
    st.session_state[f"edit_{item_id}"] = item["name"]
    st.session_state["editing_id"] = item_id


def update_item(item_id: str) -> None:
    """F2: 수정 저장. 빈 값이면 저장하지 않고 수정 모드를 유지한다."""
    name = st.session_state.get(f"edit_{item_id}", "").strip()
    if not name:
        # 수정 행 바로 아래에 표시하려고 추가 입력용 flash와 분리
        st.session_state["edit_flash"] = "아이템 이름은 비워둘 수 없습니다."
        return
    item = find_item(item_id)
    if item is not None:
        item["name"] = name
    cancel_edit()


def cancel_edit() -> None:
    """F2: 수정 모드 종료"""
    editing_id = st.session_state["editing_id"]
    if editing_id:
        st.session_state.pop(f"edit_{editing_id}", None)
    st.session_state["editing_id"] = None
    st.session_state.pop("edit_flash", None)


def delete_item(item_id: str) -> None:
    """F3: 아이템 삭제. 수정 중인 항목이면 수정 상태도 초기화한다."""
    if st.session_state["editing_id"] == item_id:
        st.session_state["editing_id"] = None
    st.session_state["items"] = [
        i for i in st.session_state["items"] if i["id"] != item_id
    ]
    drop_widget_keys(item_id)


def toggle_item(item_id: str) -> None:
    """F4: 체크 상태 토글"""
    item = find_item(item_id)
    if item is not None:
        item["checked"] = not item["checked"]


def clear_checked() -> None:
    """F5: 체크된 항목 일괄 삭제"""
    for item in [i for i in st.session_state["items"] if i["checked"]]:
        delete_item(item["id"])


# ---- 스타일 (CSS는 이 한 곳에 모은다) ----

CSS = """
<style>
/* 전체 폭/여백 */
.block-container { max-width: 640px; padding-top: 3rem; padding-bottom: 3rem; }

/* 헤더 */
h1 { font-size: 2rem !important; padding: 0 !important; }
.app-sub { opacity: .65; margin: -.25rem 0 1.25rem; }

/* 입력 폼: 테두리/여백 제거 */
[data-testid="stForm"] { padding: 0; border: 0; }

/* 목록 카드 */
[class*="st-key-row"] {
    border-radius: 12px;
    padding: .35rem .75rem;
    margin-bottom: -.25rem;
}
[class*="st-key-rowdone_"] label p { opacity: .5; }

/* 긴 이름은 말줄임 대신 줄바꿈 (공백 없는 긴 문자열도 줄바꿈) */
[class*="st-key-row"] .stMarkdownEllipsis {
    white-space: normal;
    overflow: visible;
    text-overflow: clip;
}
[class*="st-key-row"] .stMarkdownEllipsis p {
    white-space: normal;
    overflow-wrap: anywhere;
}

/* 행의 버튼: 터치 영역 44px 이상 */
[class*="st-key-row"] button {
    position: relative;
    min-height: 2.75rem;
    padding: .15rem .5rem;
    width: 100%;
}

/* 아이콘 버튼: 글자는 시각적으로만 숨기고 접근성 이름(수정/삭제)은 유지 */
[class*="st-key-rowtodo_"] button [data-testid="stMarkdownContainer"],
[class*="st-key-rowdone_"] button [data-testid="stMarkdownContainer"] {
    position: absolute;
    width: 1px;
    height: 1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
    white-space: nowrap;
}

/* 아이콘 버튼 컬럼은 폭 고정(44px), 이름 컬럼이 나머지를 차지 */
[class*="st-key-rowtodo_"] [data-testid="stColumn"]:not(:first-child),
[class*="st-key-rowdone_"] [data-testid="stColumn"]:not(:first-child) {
    flex: 0 0 2.75rem !important;
    width: 2.75rem !important;
    min-width: 2.75rem !important;
}
[class*="st-key-rowtodo_"] [data-testid="stColumn"]:first-child,
[class*="st-key-rowdone_"] [data-testid="stColumn"]:first-child {
    flex: 1 1 0 !important;
    width: auto !important;
}

/* 컬럼이 좁은 화면에서도 한 줄 유지 (Streamlit 기본은 세로로 쌓임) */
[data-testid="stHorizontalBlock"] { flex-wrap: nowrap !important; gap: .5rem; }
[data-testid="stColumn"] { min-width: 0 !important; }

/* 진행 현황 */
[data-testid="stProgress"] { margin: .25rem 0 1rem; }

/* 빈 목록 */
.empty { text-align: center; padding: 2.5rem 1rem; opacity: .7; }
.empty .icon { font-size: 2.75rem; line-height: 1; margin-bottom: .5rem; }

@media (max-width: 640px) {
    .block-container { padding-left: 1rem; padding-right: 1rem; padding-top: 4rem; }
    h1 { font-size: 1.6rem !important; }
}
</style>
"""


# ---- 화면 ----

def render_header() -> None:
    st.markdown(CSS, unsafe_allow_html=True)
    st.title("🛒 쇼핑 리스트")
    st.markdown('<p class="app-sub">오늘 살 것들을 적어보세요</p>', unsafe_allow_html=True)


def render_input() -> None:
    with st.form("add_form", clear_on_submit=True, border=False):
        col_input, col_btn = st.columns([5, 1.4], vertical_alignment="bottom")
        col_input.text_input(
            "아이템",
            key="new_name",
            placeholder="예) 우유 2개",
            label_visibility="collapsed",
        )
        col_btn.form_submit_button(
            "추가", on_click=add_item, type="primary", width="stretch"
        )

    flash = st.session_state.pop("flash", None)
    if flash:
        st.warning(flash)


def render_progress() -> None:
    items = st.session_state["items"]
    total = len(items)
    done = sum(1 for i in items if i["checked"])
    st.progress(done / total if total else 0.0, text=f"전체 {total}개 중 {done}개 완료")


def render_row(item: dict) -> None:
    item_id = item["id"]

    if st.session_state["editing_id"] == item_id:
        with st.container(border=True, key=f"rowedit_{item_id}"):
            # 폼으로 감싸 입력창에서 Enter를 누르면 저장(첫 번째 제출 버튼)되게 한다
            with st.form(f"editform_{item_id}", border=False):
                col_name, col_save, col_cancel = st.columns([5, 1.3, 1.3], vertical_alignment="center")
                col_name.text_input(
                    "이름 수정",
                    key=f"edit_{item_id}",
                    label_visibility="collapsed",
                )
                col_save.form_submit_button("저장", on_click=update_item, args=(item_id,), type="primary", width="stretch")
                col_cancel.form_submit_button("취소", on_click=cancel_edit, width="stretch")
            edit_flash = st.session_state.pop("edit_flash", None)
            if edit_flash:
                st.warning(edit_flash)
        return

    # 체크 여부에 따라 컨테이너 key 접두어를 달리해 CSS로 흐리게 처리
    prefix = "rowdone" if item["checked"] else "rowtodo"
    with st.container(border=True, key=f"{prefix}_{item_id}"):
        col_chk, col_edit, col_del = st.columns([6, 1, 1], vertical_alignment="center")
        label = escape_md(item["name"])
        if item["checked"]:
            label = f"~~{label}~~"
        col_chk.checkbox(
            label,
            value=item["checked"],
            key=f"chk_{item_id}",
            on_change=toggle_item,
            args=(item_id,),
        )
        col_edit.button("수정", key=f"editbtn_{item_id}", icon=":material/edit:", on_click=start_edit, args=(item_id,), help="수정", type="tertiary", width="stretch")
        col_del.button("삭제", key=f"del_{item_id}", icon=":material/delete:", on_click=delete_item, args=(item_id,), help="삭제", type="tertiary", width="stretch")


def render_list() -> None:
    items = st.session_state["items"]
    if not items:
        st.markdown(  # F7
            '<div class="empty"><div class="icon">🧺</div>'
            "아직 아이템이 없어요.<br>위에서 추가해보세요!</div>",
            unsafe_allow_html=True,
        )
        return
    for item in items:
        render_row(item)


def render_footer() -> None:
    has_checked = any(i["checked"] for i in st.session_state["items"])
    st.button(
        "완료 항목 삭제",
        on_click=clear_checked,
        disabled=not has_checked,
        type="tertiary",
        icon=":material/delete_sweep:",
    )


def main() -> None:
    init_state()
    render_header()
    render_input()
    render_progress()
    render_list()
    render_footer()


main()

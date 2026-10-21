import sys

import streamlit as st

import persistence
import ui

st.set_page_config(page_title="Model sign-off exercise", layout="wide")

# The banner is a CSS background-image, so the browser fetches it natively and it
# can't go through stlite's patched fetch. Under stlite (Pyodide) no server answers
# /app/static/, so point at a raw GitHub file; with a real server use the static path.
# The static path is deliberately relative (no leading slash): on Community Cloud the app
# sits in an iframe under /~/+/, and a root-relative URL would miss the app's server.
# TODO: replace this placeholder URL once the deployment repository is decided.
_UNDER_STLITE = sys.platform == "emscripten"
_BANNER_URL = (
    "https://raw.githubusercontent.com/bergam0t/nhs_oa_vidigi_streamlit/main/static/banner.png"
    if _UNDER_STLITE
    else "app/static/banner.png"
)

ui.load_css()

# Banner across the top navigation bar. Styles-only st.html goes to the hidden event
# container and applies globally.
st.html(
    """
    <style>
    header[data-testid="stHeader"] {
        height: 5rem;
        background-image:
            linear-gradient(rgba(0, 0, 0, 0.38), rgba(0, 0, 0, 0.38)),
            url("__BANNER_URL__");
        background-size: 100vw auto;
        background-position: left center;
        background-repeat: no-repeat;
    }
    header[data-testid="stHeader"] [data-testid="stToolbar"] a,
    header[data-testid="stHeader"] [data-testid="stToolbar"] a span,
    header[data-testid="stHeader"] [data-testid="stToolbar"] button,
    header[data-testid="stHeader"] [data-testid="stToolbar"] svg {
        color: #ffffff !important;
        fill: #ffffff !important;
    }
    header[data-testid="stHeader"] a[data-testid="stTopNavLink"] { font-weight: 500; }
    header[data-testid="stHeader"] a[data-testid="stTopNavLink"]:hover {
        background: rgba(255, 255, 255, 0.16);
    }
    header[data-testid="stHeader"] a[data-testid="stTopNavLink"][aria-current="page"] {
        background: rgba(255, 255, 255, 0.26);
        font-weight: 700;
    }
    /* The localStorage component renders invisible iframes; don't let them take up space. */
    .element-container:has(iframe[title*="st_local_storage"]),
    [data-testid="stElementContainer"]:has(iframe[title*="st_local_storage"]) {
        height: 0 !important;
        margin: 0 !important;
        overflow: hidden;
    }
    </style>
    """.replace("__BANNER_URL__", _BANNER_URL)
)

# Browser-local persistence, so a refresh, dropped connection or app restart doesn't wipe a
# group's answers. The store renders a hidden component once per run; if the component isn't
# installed, or we're under stlite, it's a no-op.
progress_store = persistence.get_store()

# Per-user state shared across pages: plain keys, not widget keys (widget state is
# dropped when its page isn't rendered). Saved progress is then layered on top.
ui.init_state()
persistence.load_into_session(progress_store)

pages = [
    st.Page("app_pages/briefing.py", title="0. Briefing", icon=":material/assignment:", default=True),
    st.Page("app_pages/is_it_any_good.py", title="1. Performance", icon=":material/query_stats:"),
    st.Page("app_pages/too_good.py", title="2. Issues", icon=":material/search_check:"),
    st.Page("app_pages/who_would_we_phone.py", title="3. Tradeoffs", icon=":material/format_list_numbered:"),
    st.Page("app_pages/what_will_we_do.py", title="4. Usage", icon=":material/call:"),
    st.Page("app_pages/bringing_people.py", title="5. Communication", icon=":material/groups:"),
    st.Page("app_pages/sign_off.py", title="6. Sign-off", icon=":material/task_alt:"),
]
pg = st.navigation(pages, position="top")

# After a refresh, return the group to the page they were on, then remember where they are now.
persistence.maybe_restore_page(pg, {p.url_path: p for p in pages})
persistence.record_current_page(pg)

persistence.render_reset_button()

pg.run()

# Save any changes made during this run (only writes when something changed).
persistence.save(progress_store)

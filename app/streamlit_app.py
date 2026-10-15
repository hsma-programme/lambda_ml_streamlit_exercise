import sys

import streamlit as st

import persistence
import ui

st.set_page_config(page_title="Model sign-off exercise", layout="wide")

# The banner is a CSS background-image, so the browser fetches it natively and it
# can't go through stlite's patched fetch. Under stlite (Pyodide) no server answers
# /app/static/, so point at a raw GitHub file; with a real server use the static path.
# TODO: replace this placeholder URL once the deployment repository is decided.
_UNDER_STLITE = sys.platform == "emscripten"
_BANNER_URL = (
    "https://raw.githubusercontent.com/bergam0t/nhs_oa_vidigi_streamlit/main/static/banner.png"
    if _UNDER_STLITE
    else "/app/static/banner.png"
)
_SITE_URL = "https://hsma.co.uk"

# Material "language" globe, as a percent-encoded SVG for a CSS mask (the HTML
# sanitiser strips inline SVG).
_WEB_ICON = (
    "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E"
    "%3Cpath d='M11.99 2C6.47 2 2 6.48 2 12s4.47 10 9.99 10C17.52 22 22 17.52 22 12S17.52 "
    "2 11.99 2zm6.93 6h-2.95c-.32-1.25-.78-2.45-1.38-3.56 1.84.63 3.37 1.91 4.33 3.56zM12 "
    "4.04c.83 1.2 1.48 2.53 1.91 3.96h-3.82c.43-1.43 1.08-2.76 1.91-3.96zM4.26 14C4.1 13.36 "
    "4 12.69 4 12s.1-1.36.26-2h3.38c-.08.66-.14 1.32-.14 2 0 .68.06 1.34.14 2H4.26zm.82 "
    "2h2.95c.32 1.25.78 2.45 1.38 3.56-1.84-.63-3.37-1.9-4.33-3.56zm2.95-8H5.08c.96-1.66 "
    "2.49-2.93 4.33-3.56C8.81 5.55 8.35 6.75 8.03 8zM12 19.96c-.83-1.2-1.48-2.53-1.91-3.96"
    "h3.82c-.43 1.43-1.08 2.76-1.91 3.96zM14.34 14H9.66c-.09-.66-.16-1.32-.16-2 0-.68.07-1.35"
    ".16-2h4.68c.09.65.16 1.32.16 2 0 .68-.07 1.34-.16 2zm.25 5.56c.6-1.11 1.06-2.31 "
    "1.38-3.56h2.95c-.96 1.65-2.49 2.93-4.33 3.56zM16.36 14c.08-.66.14-1.32.14-2 0-.68-.06"
    "-1.34-.14-2h3.38c.16.64.26 1.31.26 2s-.1 1.36-.26 2h-3.38z'/%3E%3C/svg%3E"
)

ui.load_css()

# Banner across the top navigation bar and the icon link on top of it. Styles-only
# st.html goes to the hidden event container and applies globally, so the content
# block below is kept separate.
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
    .top-bar-links {
        position: fixed;
        top: 0;
        right: 4.5rem;
        height: 5rem;
        display: flex;
        align-items: center;
        z-index: 999991;
    }
    .top-bar-links a {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 2.5rem;
        height: 2.5rem;
        border-radius: 0.5rem;
        color: #ffffff;
    }
    .top-bar-links a:hover { background: rgba(255, 255, 255, 0.16); }
    .top-bar-links .icon {
        display: block;
        width: 1.5rem;
        height: 1.5rem;
        background-color: currentColor;
        -webkit-mask-repeat: no-repeat;
        mask-repeat: no-repeat;
        -webkit-mask-position: center;
        mask-position: center;
        -webkit-mask-size: contain;
        mask-size: contain;
        -webkit-mask-image: url("__WEB_ICON__");
        mask-image: url("__WEB_ICON__");
    }
    </style>
    """.replace("__BANNER_URL__", _BANNER_URL).replace("__WEB_ICON__", _WEB_ICON)
)

st.html(
    f"""
    <div class="top-bar-links">
        <a href="{_SITE_URL}" target="_blank" title="Visit hsma.co.uk"
           aria-label="Visit hsma.co.uk">
            <span class="icon"></span>
        </a>
    </div>
    """
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
    st.Page("app_pages/is_it_any_good.py", title="1. Is it any good?", icon=":material/query_stats:"),
    st.Page("app_pages/too_good.py", title="2. Too good to be true?", icon=":material/search_check:"),
    st.Page("app_pages/what_will_we_do.py", title="3. What will we do with it?", icon=":material/call:"),
    st.Page("app_pages/bringing_people.py", title="4. Bringing people with you", icon=":material/groups:"),
    st.Page("app_pages/sign_off.py", title="5. Sign-off", icon=":material/task_alt:"),
]
pg = st.navigation(pages, position="top")

# After a refresh, return the group to the page they were on, then remember where they are now.
persistence.maybe_restore_page(pg, {p.url_path: p for p in pages})
persistence.record_current_page(pg)

persistence.render_reset_button()

pg.run()

# Save any changes made during this run (only writes when something changed).
persistence.save(progress_store)

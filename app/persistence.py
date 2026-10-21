"""Browser-local persistence of a group's progress.

Ported from the geographic OR/DS playground (app/persistence.py there), adapted for this app.

Every decision a group makes lives under plain keys in ``st.session_state``. That is wiped
when the page is refreshed, the connection drops, or a Community Cloud container restarts.
To survive those, the small JSON-serialisable slice listed in ``progress_keys()`` is mirrored
into the browser's ``localStorage`` (via the optional ``streamlit-local-storage`` component)
and restored on load. Nothing is sent to or kept on the server.

Everything goes through a small ``ProgressStore`` seam. If the component isn't installed, or
the app is running under stlite (where a component may never mount), ``get_store()`` returns
a ``NullStore`` and the app runs exactly as before, just without persistence.
"""

from __future__ import annotations

import json
import sys
from typing import Protocol

import streamlit as st

# Bump if the shape of the saved data changes so that old blobs are unsafe to restore;
# mismatched versions are then discarded.
SCHEMA_VERSION = 1

# The single localStorage key holding the whole JSON blob.
STORAGE_KEY = "readmitrisk_progress_v1"

# The page the group is on, saved so a refresh returns them there.
CURRENT_PAGE_KEY = "current_page"

# Session-state bookkeeping (not itself saved).
_HYDRATED_FLAG = "_progress_hydrated"
_READ_ATTEMPTS = "_progress_read_attempts"
_LAST_SAVED_HASH = "_progress_last_saved"
_STORE_HANDLE = "_progress_store"
_PAGE_RESTORED = "_progress_page_restored"

START_PAGE = "app_pages/briefing.py"


def progress_keys() -> list[str]:
    """The session-state keys that make up a group's progress. All must be JSON-serialisable."""
    return [
        # Stage 0
        "initial_verdict",
        "initial_reason",
        # Stage 1
        "baseline_guess",
        "auc_pairs",
        "auc_shown",
        "auc_check",
        # Stage 2
        "capacity_choice",
        "capacity_recorded",
        "tradeoff_choice",
        # Stage 3. Keys named after a stage (stage2_verdict, stage4_statements) keep the numbering
        # from before "Who would we phone?" became its own page, so saved progress still loads.
        "known_answers",
        "v2_shown",
        "stage2_verdict",
        # Stage 4
        "interventions",
        # Stage 5
        "stage4_statements",
        # Stage 6
        "final_verdict",
        "final_reason",
        "conditions",
        "owner",
        "pause_criteria",
        # Where they were
        CURRENT_PAGE_KEY,
    ]


def snapshot() -> dict:
    """Read the saved slice of session state into a plain dict."""
    return {k: st.session_state[k] for k in progress_keys() if k in st.session_state}


def restore(data: dict) -> None:
    """Write a previously saved snapshot back into session state."""
    for k in progress_keys():
        if k in data:
            st.session_state[k] = data[k]


#############################
# MARK: Store implementations
#############################
class ProgressStore(Protocol):
    def read(self) -> dict | None: ...
    def write(self, data: dict) -> None: ...
    def clear(self) -> None: ...


class NullStore:
    """Used when the localStorage component is unavailable: persistence off."""

    def read(self) -> dict | None:
        return None

    def write(self, data: dict) -> None:
        pass

    def clear(self) -> None:
        pass


class BrowserStore:
    """Keeps the JSON blob in the browser, using the ``streamlit-local-storage`` component.

    This calls the library's component function directly rather than its ``LocalStorage``
    class: that class busy-waits until the browser answers, which freezes the app if the
    component never mounts (seen under AppTest, and possible in a locked-down browser).
    Here the first run simply sees nothing yet, and ``load_into_session`` gives it a second
    run to answer, as before.
    """

    def __init__(self, component):
        self._c = component
        # Every item in this browser's localStorage, or None until the component has answered.
        self._items = component(method="getAll", key="readmitrisk_storage_getall", default=None)

    def read(self) -> dict | None:
        if not isinstance(self._items, dict):
            return None
        raw = self._items.get(STORAGE_KEY)
        if not raw:
            return None
        try:
            blob = json.loads(raw) if isinstance(raw, str) else raw
        except (json.JSONDecodeError, TypeError):
            return None
        if not isinstance(blob, dict) or blob.get("v") != SCHEMA_VERSION:
            return None
        data = blob.get("data")
        return data if isinstance(data, dict) else None

    def write(self, data: dict) -> None:
        payload = json.dumps({"v": SCHEMA_VERSION, "data": data})
        self._c(method="setItem", itemKey=STORAGE_KEY, itemValue=payload, key="readmitrisk_progress_set")

    def clear(self) -> None:
        # The library's deleteItem only changes the stored default; eraseItem removes the item.
        self._c(method="eraseItem", itemKey=STORAGE_KEY, key="readmitrisk_progress_erase", default=None)


def get_store() -> ProgressStore:
    """Build the per-run store, falling back to a no-op if the component is missing or the
    app is running under stlite."""
    if sys.platform == "emscripten":
        # A component may never mount under stlite, so don't try.
        return NullStore()
    try:
        from streamlit_local_storage import _st_local_storage
    except ImportError:
        return NullStore()

    store = BrowserStore(_st_local_storage)
    # Stashed so the reset control can reuse the same store.
    st.session_state[_STORE_HANDLE] = store
    return store


#############################
# MARK: Session integration
#############################
def load_into_session(store: ProgressStore) -> None:
    """Restore a saved snapshot onto session state, at most once per session.

    The component can return nothing on the first script run while it mounts, then the stored
    value on the next run, so give it two runs before treating the session as genuinely new.
    """
    if st.session_state.get(_HYDRATED_FLAG):
        return

    data = store.read()
    if data:
        restore(data)
        st.session_state[_HYDRATED_FLAG] = True
        return

    attempts = st.session_state.get(_READ_ATTEMPTS, 0) + 1
    st.session_state[_READ_ATTEMPTS] = attempts
    if attempts >= 2:
        st.session_state[_HYDRATED_FLAG] = True


def save(store: ProgressStore) -> None:
    """Write the current snapshot, but only when it has changed, and never before loading
    (or a fresh session could overwrite saved progress before it has been read back)."""
    if not st.session_state.get(_HYDRATED_FLAG):
        return

    data = snapshot()
    digest = json.dumps(data, sort_keys=True, default=str)
    if st.session_state.get(_LAST_SAVED_HASH) == digest:
        return

    store.write(data)
    st.session_state[_LAST_SAVED_HASH] = digest


def maybe_restore_page(current_page, pages_by_path: dict) -> None:
    """After progress is restored, return the group to the page they were on, once."""
    if not st.session_state.get(_HYDRATED_FLAG):
        return
    if st.session_state.get(_PAGE_RESTORED):
        return
    st.session_state[_PAGE_RESTORED] = True

    saved = st.session_state.get(CURRENT_PAGE_KEY)
    if saved and saved != current_page.url_path:
        target = pages_by_path.get(saved)
        if target is not None:
            st.switch_page(target)


def record_current_page(current_page) -> None:
    """Remember which page is being shown, so it can be restored next session."""
    st.session_state[CURRENT_PAGE_KEY] = current_page.url_path


def reset_progress(store: ProgressStore | None = None) -> None:
    """Clear the group's progress from both session state and the browser."""
    if store is None:
        store = st.session_state.get(_STORE_HANDLE) or NullStore()

    # Clear everything the group touched, including widget values, so no old answer is shown
    # again. Keep only the bookkeeping that ties this session to the browser component.
    keep = {_STORE_HANDLE, _HYDRATED_FLAG, _READ_ATTEMPTS, _PAGE_RESTORED}
    for k in list(st.session_state.keys()):
        if k not in keep and not k.startswith("start_over") and not k.startswith("readmitrisk_"):
            st.session_state.pop(k, None)
    store.clear()


def render_reset_button() -> None:
    """A small, confirm-gated "Start over" control at the top right of every page."""
    with st.container(horizontal=True, horizontal_alignment="right", key="start_over_bar"):
        with st.popover("Start over", icon=":material/restart_alt:"):
            st.markdown(
                "This clears your group's answers **on this device** and takes you back to the Briefing. "
                "It can't be undone."
            )
            if st.button("Yes, clear our answers", key="start_over_confirm", type="primary"):
                reset_progress()
                st.switch_page(START_PAGE)

import streamlit as st
import pandas as pd

from core.database import append_csv, read_csv

try:
    from core.common import log_event
except Exception:
    log_event = None


# ============================================================
# SAFE HELPERS
# ============================================================

def _now():
    return pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")


def safe_df(name):
    try:
        df = read_csv(name)
        if df is None or not isinstance(df, pd.DataFrame):
            return pd.DataFrame()
        return df
    except Exception as e:
        st.warning(f"Could not load {name}: {e}")
        return pd.DataFrame()


def safe_append(name, row):
    try:
        append_csv(name, row)
        return True
    except Exception as e:
        st.error(f"Could not save to {name}: {e}")
        return False


def safe_log(msg):
    try:
        if log_event:
            log_event(msg)
            return
    except Exception:
        pass

    st.session_state.setdefault("activity_log", [])
    st.session_state.activity_log.insert(
        0,
        {"time": _now(), "event": str(msg)},
    )


def init_profile_state():
    defaults = {
        "notes": [],
        "activity_log": [],
        "profile_name": "Quant Trader",
        "phone_mode": False,
        "profile_goal": "12H Hold Strategy",
        "risk_mode": "Balanced",
        "setting_auto_entry": True,
        "setting_exit_alerts": True,
        "setting_risk_active": True,
        "setting_phone_mode": False,
    }

    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def download_button(df, label, filename):
    if isinstance(df, pd.DataFrame) and not df.empty:
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label=label,
            data=csv,
            file_name=filename,
            mime="text/csv",
            use_container_width=True,
        )


def filter_df(df, search_text=""):
    if df is None or not isinstance(df, pd.DataFrame) or df.empty:
        return pd.DataFrame()

    out = df.copy()

    if str(search_text).strip():
        s = str(search_text).strip().lower()
        mask = out.astype(str).apply(
            lambda col: col.str.lower().str.contains(s, na=False)
        ).any(axis=1)
        out = out[mask]

    return out


def data_health_box(name, df):
    rows = 0 if df is None else len(df)
    cols = 0 if df is None or df.empty else len(df.columns)

    if rows == 0:
        status = "EMPTY"
        icon = "⚠️"
    elif rows < 20:
        status = "LOW DATA"
        icon = "🟡"
    else:
        status = "READY"
        icon = "🟢"

    st.metric(f"{icon} {name}", f"{rows} rows", f"{cols} cols / {status}")


# ============================================================
# MAIN PROFILE TAB
# ============================================================

def show():
    init_profile_state()

    st.markdown("# 👤 Profile Dashboard")

    t1, t2, t3, t4 = st.tabs([
        "Trader Profile",
        "Data Health",
        "Notes",
        "Activity Log",
    ])

    # ========================================================
    # TAB 1 — PROFILE SETTINGS
    # ========================================================
    with t1:
        st.subheader("Trader Profile")

        c1, c2 = st.columns(2)

        with c1:
            st.session_state.profile_name = st.text_input(
                "Profile Name",
                value=st.session_state.profile_name,
                key="profile_name_input",
            )

            st.session_state.profile_goal = st.text_input(
                "Main Trading Goal",
                value=st.session_state.profile_goal,
                key="profile_goal_input",
            )

        with c2:
            st.session_state.risk_mode = st.selectbox(
                "Risk Mode",
                ["Safe", "Balanced", "Aggressive"],
                index=["Safe", "Balanced", "Aggressive"].index(
                    st.session_state.get("risk_mode", "Balanced")
                ),
                key="risk_mode_input",
            )

            st.session_state.setting_phone_mode = st.toggle(
                "Phone Mode",
                value=bool(st.session_state.get("setting_phone_mode", False)),
                key="setting_phone_mode_input",
            )

        st.markdown("### System Settings")

        c3, c4, c5 = st.columns(3)

        with c3:
            st.session_state.setting_auto_entry = st.toggle(
                "Auto Entry Assist",
                value=bool(st.session_state.setting_auto_entry),
            )

        with c4:
            st.session_state.setting_exit_alerts = st.toggle(
                "Exit Alerts",
                value=bool(st.session_state.setting_exit_alerts),
            )

        with c5:
            st.session_state.setting_risk_active = st.toggle(
                "Risk Protection",
                value=bool(st.session_state.setting_risk_active),
            )

        if st.button("💾 Save Profile Settings", use_container_width=True):
            row = {
                "time": _now(),
                "profile_name": st.session_state.profile_name,
                "profile_goal": st.session_state.profile_goal,
                "risk_mode": st.session_state.risk_mode,
                "phone_mode": st.session_state.setting_phone_mode,
                "auto_entry": st.session_state.setting_auto_entry,
                "exit_alerts": st.session_state.setting_exit_alerts,
                "risk_active": st.session_state.setting_risk_active,
            }

            if safe_append("profile_settings", row):
                safe_log("Profile settings saved")
                st.success("Profile settings saved")

    # ========================================================
    # TAB 2 — DATA HEALTH
    # ========================================================
    with t2:
        st.subheader("Data Health")

        files = {
            "Training Data": safe_df("training_data"),
            "Backtest Results": safe_df("backtest_results"),
            "Risk Plans": safe_df("risk_plans"),
            "Risk Snapshots": safe_df("risk_snapshots"),
            "Mix History": safe_df("mix_history"),
            "Advanced Risk Checks": safe_df("advanced_risk_checks"),
            "Profile Settings": safe_df("profile_settings"),
            "Profile Notes": safe_df("profile_notes"),
        }

        c = st.columns(2)
        i = 0

        for name, df in files.items():
            with c[i % 2]:
                data_health_box(name, df)
            i += 1

        st.markdown("### Search Saved Data")

        selected = st.selectbox("Choose data file", list(files.keys()))
        search_text = st.text_input("Search text")

        selected_df = filter_df(files[selected], search_text)

        if selected_df.empty:
            st.info("No data found.")
        else:
            st.dataframe(selected_df.tail(300), use_container_width=True)
            download_button(
                selected_df,
                f"⬇️ Download {selected}",
                f"{selected.lower().replace(' ', '_')}.csv",
            )

    # ========================================================
    # TAB 3 — NOTES
    # ========================================================
    with t3:
        st.subheader("Trading Notes")

        note = st.text_area("Write new note", key="profile_new_note")

        if st.button("💾 Save Note", use_container_width=True):
            if note.strip():
                row = {
                    "time": _now(),
                    "profile": st.session_state.profile_name,
                    "goal": st.session_state.profile_goal,
                    "risk_mode": st.session_state.risk_mode,
                    "note": note.strip(),
                }

                if safe_append("profile_notes", row):
                    st.session_state.notes.insert(0, row)
                    safe_log("New profile note saved")
                    st.success("Note saved")
            else:
                st.warning("Write a note first.")

        notes_df = safe_df("profile_notes")

        if notes_df.empty:
            st.info("No saved notes yet.")
        else:
            st.dataframe(notes_df.tail(200), use_container_width=True)
            download_button(notes_df, "⬇️ Download Notes", "profile_notes.csv")

    # ========================================================
    # TAB 4 — ACTIVITY LOG
    # ========================================================
    with t4:
        st.subheader("Activity Log")

        log_df = pd.DataFrame(st.session_state.get("activity_log", []))

        if log_df.empty:
            st.info("No activity log yet.")
        else:
            st.dataframe(log_df.head(300), use_container_width=True)

        if st.button("🧹 Clear Session Activity Log", use_container_width=True):
            st.session_state.activity_log = []
            st.success("Session activity log cleared")
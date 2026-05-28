import streamlit as st
import pandas as pd

from core.quant_models import quant_stack, add_indicators
from core.database import read_csv, append_csv


def _safe_read_csv(name):
    try:
        df = read_csv(name)
        if df is None:
            return pd.DataFrame()
        return df
    except Exception as e:
        st.warning(f"Could not read {name}: {e}")
        return pd.DataFrame()


def _safe_append_csv(name, row):
    try:
        append_csv(name, row)
        return True
    except Exception as e:
        st.error(f"Could not save {name}: {e}")
        return False


def _safe_add_indicators(df):
    try:
        out = add_indicators(df.copy())
        if out is None:
            return df.copy()
        return out
    except Exception as e:
        st.error(f"Indicator calculation failed: {e}")
        return df.copy()


def _safe_quant_stack(df, hist, account_snapshot):
    try:
        q = quant_stack(df.copy(), hist, account_snapshot)
        if not isinstance(q, dict):
            return {
                "bias": "WAIT",
                "scale10": 0,
                "safe_pct": 0,
                "history_samples": len(hist),
                "error": "quant_stack did not return dict",
            }
        return q
    except Exception as e:
        return {
            "bias": "WAIT",
            "scale10": 0,
            "safe_pct": 0,
            "history_samples": len(hist),
            "error": str(e),
        }


def _clean_for_save(q):
    row = {}

    for k, v in q.items():
        if isinstance(v, (str, int, float, bool)) or v is None:
            row[k] = v
        else:
            row[k] = str(v)

    return row


def show():
    st.markdown("# 🧠 Mix — Advanced History Matching")

    df = st.session_state.get("last_df")

    if df is None or not isinstance(df, pd.DataFrame) or df.empty:
        st.warning(
            "Connect data from Home or Engine first. Mix will use the same persistent data and will not blank until disconnect."
        )
        return

    df = df.copy()

    backtest_df = _safe_read_csv("backtest_results")

    hist = []
    if not backtest_df.empty:
        hist.extend(backtest_df.to_dict("records"))

    session_hist = st.session_state.get("trade_history", [])
    if isinstance(session_hist, list):
        hist.extend(session_hist)

    account_snapshot = st.session_state.get("account_snapshot", {})
    if not isinstance(account_snapshot, dict):
        account_snapshot = {}

    q = _safe_quant_stack(df, hist, account_snapshot)

    bias = q.get("bias", "WAIT")
    scale10 = q.get("scale10", 0)
    safe_pct = q.get("safe_pct", 0)
    history_samples = q.get("history_samples", len(hist))

    c = st.columns(4)
    c[0].metric("Best Safe Bias", bias)
    c[1].metric("Scale /10", scale10)
    c[2].metric("Percent", safe_pct)
    c[3].metric("History Samples", history_samples)

    if "error" in q:
        st.error(f"Mix engine fallback mode: {q['error']}")

    st.markdown("### Full Mix Engine Output")
    st.json(q)

    st.markdown("### Save Decision")
    save_note = st.text_input("Optional note", key="mix_save_note")

    if st.button("💾 Save Mix Decision To Training Data", key="save_mix_training"):
        row = {
            "time": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
            "tab": "mix",
            "note": save_note,
            **_clean_for_save(q),
        }

        if _safe_append_csv("training_data", row):
            st.success("Saved to training_data")

    st.markdown("### Latest Feature Data")

    feature_df = _safe_add_indicators(df)

    if feature_df.empty:
        st.warning("No feature data available.")
    else:
        row_count = st.slider(
            "Rows to show",
            min_value=20,
            max_value=min(500, len(feature_df)),
            value=min(60, len(feature_df)),
            key="mix_rows_to_show",
        )

        st.dataframe(feature_df.tail(row_count), use_container_width=True)

        csv = feature_df.tail(row_count).to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Download Latest Feature Data",
            data=csv,
            file_name="mix_latest_feature_data.csv",
            mime="text/csv",
            use_container_width=True,
        )
import streamlit as st
import pandas as pd

from core.database import append_csv, read_csv


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


def _safe_float(value, default=0.0):
    try:
        if value is None or value == "":
            return default
        return float(value)
    except Exception:
        return default


def _risk_color_status(risk_pct, margin_level):
    if risk_pct <= 1 and margin_level >= 300:
        return "🟢 Safe"
    if risk_pct <= 2 and margin_level >= 150:
        return "🟡 Medium"
    return "🔴 High Risk"


def show():
    st.markdown("# 🛡️ Risk Tab — Original + Doo Prime Account Inner Tabs")

    t1, t2, t3, t4 = st.tabs([
        "Original Risk Calculator",
        "Doo Prime Risk",
        "Risk History",
        "Advanced Risk Check",
    ])

    # =========================
    # TAB 1 — ORIGINAL RISK
    # =========================
    with t1:
        st.subheader("Original Risk Calculator")

        c1, c2 = st.columns(2)

        with c1:
            balance = st.number_input(
                "Balance",
                min_value=0.0,
                value=1000.0,
                step=50.0,
                key="risk_balance",
            )

            risk = st.slider(
                "Risk %",
                min_value=0.1,
                max_value=10.0,
                value=1.0,
                step=0.1,
                key="risk_percent",
            )

        with c2:
            sl = st.number_input(
                "Stop loss pips",
                min_value=0.0,
                value=50.0,
                step=1.0,
                key="risk_sl_pips",
            )

            pip_value = st.number_input(
                "Pip value per 1 lot",
                min_value=0.0,
                value=10.0,
                step=0.1,
                key="risk_pip_value",
            )

        dollar_risk = balance * risk / 100
        lot = dollar_risk / (sl * pip_value) if sl > 0 and pip_value > 0 else 0

        c = st.columns(4)
        c[0].metric("Suggested Lot", round(lot, 3))
        c[1].metric("Dollar Risk", round(dollar_risk, 2))
        c[2].metric("Stop Loss Pips", round(sl, 2))
        c[3].metric("Risk %", round(risk, 2))

        if sl <= 0:
            st.warning("Stop loss must be greater than 0.")
        if pip_value <= 0:
            st.warning("Pip value must be greater than 0.")

        note = st.text_input("Optional plan note", key="risk_plan_note")

        if st.button("💾 Save Risk Plan", key="save_risk_plan", use_container_width=True):
            row = {
                "time": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
                "balance": balance,
                "risk_pct": risk,
                "sl_pips": sl,
                "pip_value": pip_value,
                "dollar_risk": dollar_risk,
                "lot": lot,
                "note": note,
            }

            if _safe_append_csv("risk_plans", row):
                st.success("Saved risk plan")

    # =========================
    # TAB 2 — DOO PRIME RISK
    # =========================
    with t2:
        st.subheader("Doo Prime Account Risk")

        info = st.session_state.get("account_snapshot", {})

        if not isinstance(info, dict) or not info:
            st.info("Read Doo Prime account inside Home first.")
        else:
            bal = _safe_float(info.get("balance", 0))
            eq = _safe_float(info.get("equity", 0))
            free = _safe_float(
                info.get("margin_free", info.get("free_margin", 0))
            )
            ml = _safe_float(
                info.get("margin_level", info.get("margin_level_percent", 0))
            )
            margin = _safe_float(info.get("margin", 0))
            profit = _safe_float(info.get("profit", 0))

            c = st.columns(4)
            c[0].metric("Balance", round(bal, 2))
            c[1].metric("Equity", round(eq, 2))
            c[2].metric("Free Margin", round(free, 2))
            c[3].metric("Margin %", round(ml, 2))

            c2 = st.columns(4)
            c2[0].metric("Used Margin", round(margin, 2))
            c2[1].metric("Floating P/L", round(profit, 2))
            c2[2].metric("Equity - Balance", round(eq - bal, 2))
            c2[3].metric("Free Margin Ratio", round((free / eq * 100), 2) if eq > 0 else 0)

            loss_room = max(0, eq - free * 0.1)
            danger_buffer = max(0, free - eq * 0.1)
            account_status = _risk_color_status(st.session_state.get("risk_percent", 1.0), ml)

            st.metric("Estimated Loss Room Before Danger", round(loss_room, 2))
            st.metric("Danger Buffer", round(danger_buffer, 2))
            st.markdown(f"### Account Status: {account_status}")

            if ml and ml < 100:
                st.error("Margin level is dangerous. Avoid new trades.")
            elif ml and ml < 150:
                st.warning("Margin level is weak. Reduce exposure.")
            elif ml >= 300:
                st.success("Margin level looks healthy.")

            if st.button("💾 Save Doo Prime Risk Snapshot", key="save_doo_risk", use_container_width=True):
                row = {
                    "time": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "balance": bal,
                    "equity": eq,
                    "free_margin": free,
                    "margin_level": ml,
                    "used_margin": margin,
                    "floating_profit": profit,
                    "loss_room": loss_room,
                    "danger_buffer": danger_buffer,
                    "status": account_status,
                }

                if _safe_append_csv("risk_snapshots", row):
                    st.success("Doo Prime risk snapshot saved")

    # =========================
    # TAB 3 — RISK HISTORY
    # =========================
    with t3:
        st.subheader("Risk History")

        risk_df = _safe_read_csv("risk_plans")
        snap_df = _safe_read_csv("risk_snapshots")

        h1, h2 = st.tabs(["Risk Plans", "Doo Prime Snapshots"])

        with h1:
            if risk_df.empty:
                st.info("No saved risk plans yet.")
            else:
                st.dataframe(risk_df.tail(300), use_container_width=True)

        with h2:
            if snap_df.empty:
                st.info("No saved Doo Prime risk snapshots yet.")
            else:
                st.dataframe(snap_df.tail(300), use_container_width=True)

    # =========================
    # TAB 4 — ADVANCED RISK CHECK
    # =========================
    with t4:
        st.subheader("Advanced Risk Check")

        balance2 = st.number_input(
            "Advanced Balance",
            min_value=0.0,
            value=float(st.session_state.get("risk_balance", 1000.0)),
            step=50.0,
            key="adv_balance",
        )

        open_trades = st.number_input(
            "Open Trades Count",
            min_value=0,
            value=0,
            step=1,
            key="adv_open_trades",
        )

        risk_per_trade = st.slider(
            "Risk Per Trade %",
            min_value=0.1,
            max_value=10.0,
            value=float(st.session_state.get("risk_percent", 1.0)),
            step=0.1,
            key="adv_risk_trade",
        )

        max_daily_loss = st.slider(
            "Max Daily Loss %",
            min_value=1.0,
            max_value=30.0,
            value=5.0,
            step=0.5,
            key="adv_daily_loss",
        )

        total_open_risk = open_trades * risk_per_trade
        daily_loss_amount = balance2 * max_daily_loss / 100
        one_trade_loss = balance2 * risk_per_trade / 100

        c = st.columns(4)
        c[0].metric("One Trade Risk $", round(one_trade_loss, 2))
        c[1].metric("Total Open Risk %", round(total_open_risk, 2))
        c[2].metric("Max Daily Loss $", round(daily_loss_amount, 2))
        c[3].metric("Remaining Trade Slots", max(0, int(max_daily_loss // risk_per_trade) - open_trades))

        if total_open_risk >= max_daily_loss:
            st.error("Open risk is already at or above your daily loss limit. Do not add new trades.")
        elif total_open_risk >= max_daily_loss * 0.7:
            st.warning("Open risk is near your daily limit. Use smaller size or wait.")
        else:
            st.success("Risk level is acceptable.")

        if st.button("💾 Save Advanced Risk Check", key="save_advanced_risk", use_container_width=True):
            row = {
                "time": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
                "balance": balance2,
                "open_trades": open_trades,
                "risk_per_trade": risk_per_trade,
                "max_daily_loss": max_daily_loss,
                "total_open_risk": total_open_risk,
                "daily_loss_amount": daily_loss_amount,
                "one_trade_loss": one_trade_loss,
            }

            if _safe_append_csv("advanced_risk_checks", row):
                st.success("Advanced risk check saved")
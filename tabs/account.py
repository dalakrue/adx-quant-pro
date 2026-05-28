import streamlit as st
import pandas as pd
import math
from datetime import datetime

from core.data_connectors import get_mt5_account_snapshot
from core.database import append_event


# ==========================================================
# SAFE HELPERS
# ==========================================================

def _safe_append_event(event_type, payload):
    """
    Prevent database/logging errors from crashing the Streamlit app.
    """
    try:
        append_event(event_type, payload)
    except Exception:
        pass


def _safe_float(value, default=0.0):
    """
    Convert MT5 values safely to float.
    """
    try:
        if value is None:
            return default
        value = float(value)
        if math.isnan(value) or math.isinf(value):
            return default
        return value
    except Exception:
        return default


def _safe_int(value, default=0):
    """
    Convert MT5 values safely to int.
    """
    try:
        if value is None:
            return default
        return int(value)
    except Exception:
        return default


def _fmt_money(value):
    return round(_safe_float(value), 2)


def _fmt_percent(value):
    return round(_safe_float(value), 2)


def _format_hold_time(minutes):
    """
    Convert minutes into readable hold time.
    """
    minutes = _safe_float(minutes)

    if minutes <= 0:
        return "00h 00m"

    total_minutes = int(minutes)
    days = total_minutes // 1440
    hours = (total_minutes % 1440) // 60
    mins = total_minutes % 60

    if days > 0:
        return f"{days}d {hours:02d}h {mins:02d}m"

    return f"{hours:02d}h {mins:02d}m"


def _position_type_text(position_type):
    """
    MT5 position type:
    0 = BUY
    1 = SELL
    """
    try:
        position_type = int(position_type)
        if position_type == 0:
            return "BUY"
        if position_type == 1:
            return "SELL"
    except Exception:
        pass

    return str(position_type)


def _normalize_position_record(pos):
    """
    Convert MT5 position object / namedtuple / dict into normal dict.
    """
    if isinstance(pos, dict):
        return pos

    if hasattr(pos, "_asdict"):
        return pos._asdict()

    try:
        return dict(pos)
    except Exception:
        pass

    # Last fallback for object-like MT5 data
    result = {}
    for key in dir(pos):
        if key.startswith("_"):
            continue
        try:
            value = getattr(pos, key)
            if not callable(value):
                result[key] = value
        except Exception:
            pass

    return result


def _positions_df(positions):
    """
    Build a clean dataframe from MT5 positions safely.
    """
    if not positions:
        return pd.DataFrame()

    try:
        rows = [_normalize_position_record(p) for p in positions]
        df = pd.DataFrame(rows)
    except Exception:
        return pd.DataFrame()

    if df.empty:
        return df

    # Convert MT5 timestamp columns
    for col in ["time", "time_update"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], unit="s", errors="coerce")

    # Convert milliseconds timestamps if available
    for col in ["time_msc", "time_update_msc"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], unit="ms", errors="coerce")

    return df


def _guess_pip_size(symbol, price_open=None):
    """
    Estimate pip size from symbol name and price.
    This is safer than the old proxy formula.
    """
    symbol = str(symbol or "").upper()
    price_open = _safe_float(price_open)

    # JPY pairs usually use 0.01 pip
    if "JPY" in symbol:
        return 0.01

    # Gold / XAU often behaves better with 0.1 as pip-like move
    if "XAU" in symbol or "GOLD" in symbol:
        return 0.1

    # Silver
    if "XAG" in symbol or "SILVER" in symbol:
        return 0.01

    # BTC / crypto proxy
    if "BTC" in symbol or "ETH" in symbol or "CRYPTO" in symbol:
        return 1.0

    # Normal forex major/minor
    if price_open > 0:
        if price_open >= 100:
            return 0.01
        return 0.0001

    return 0.0001


def _calculate_pips(row):
    """
    Calculate pip movement correctly for BUY and SELL.
    BUY: current - open
    SELL: open - current
    """
    price_open = _safe_float(row.get("price_open"))
    price_current = _safe_float(row.get("price_current"))
    position_type = _safe_int(row.get("type"), -1)
    symbol = row.get("symbol", "")

    if price_open <= 0 or price_current <= 0:
        return 0.0

    pip_size = _guess_pip_size(symbol, price_open)

    if position_type == 0:      # BUY
        pips = (price_current - price_open) / pip_size
    elif position_type == 1:    # SELL
        pips = (price_open - price_current) / pip_size
    else:
        pips = (price_current - price_open) / pip_size

    return round(pips, 1)


def _upgrade_positions_df(df, account):
    """
    Add useful analysis columns:
    - side
    - hold minutes
    - hold time text
    - pips
    - profit percent of equity
    - profit per 0.01 lot
    - risk status
    """
    if df.empty:
        return df

    df = df.copy()
    now = pd.Timestamp.now()

    if "type" in df.columns:
        df["side"] = df["type"].apply(_position_type_text)

    if "time" in df.columns:
        df["hold_minutes"] = (now - df["time"]).dt.total_seconds() / 60
        df["hold_time"] = df["hold_minutes"].apply(_format_hold_time)

    if "price_open" in df.columns and "price_current" in df.columns:
        df["pips"] = df.apply(_calculate_pips, axis=1)

    equity = max(_safe_float(account.get("equity"), 1.0), 1.0)

    if "profit" in df.columns:
        df["profit"] = df["profit"].apply(_safe_float)
        df["profit_pct_of_equity"] = (df["profit"] / equity * 100).round(2)

    if "volume" in df.columns and "profit" in df.columns:
        df["volume"] = df["volume"].apply(_safe_float)
        df["profit_per_0.01_lot"] = df.apply(
            lambda r: round(_safe_float(r.get("profit")) / max(_safe_float(r.get("volume")), 0.01) * 0.01, 2),
            axis=1
        )

    # Simple status label
    if "profit" in df.columns:
        def status(x):
            x = _safe_float(x)
            if x > 0:
                return "Profit"
            if x < 0:
                return "Loss"
            return "Flat"

        df["status"] = df["profit"].apply(status)

    return df


def _account_risk_summary(account, positions):
    """
    Calculate useful account risk numbers.
    """
    balance = _safe_float(account.get("balance"))
    equity = _safe_float(account.get("equity"))
    margin = _safe_float(account.get("margin"))
    free_margin = _safe_float(account.get("margin_free"))
    margin_level = _safe_float(account.get("margin_level"))

    floating_pl = 0.0
    if not positions.empty and "profit" in positions.columns:
        floating_pl = _safe_float(positions["profit"].sum())

    drawdown_money = max(balance - equity, 0.0)
    drawdown_pct = (drawdown_money / balance * 100) if balance > 0 else 0.0

    used_margin_pct = (margin / equity * 100) if equity > 0 else 0.0
    free_margin_pct = (free_margin / equity * 100) if equity > 0 else 0.0

    if margin_level <= 0:
        danger = "Unknown"
    elif margin_level < 100:
        danger = "Extreme danger"
    elif margin_level < 200:
        danger = "High danger"
    elif margin_level < 500:
        danger = "Medium"
    else:
        danger = "Healthy"

    return {
        "balance": balance,
        "equity": equity,
        "margin": margin,
        "free_margin": free_margin,
        "margin_level": margin_level,
        "floating_pl": floating_pl,
        "drawdown_money": drawdown_money,
        "drawdown_pct": drawdown_pct,
        "used_margin_pct": used_margin_pct,
        "free_margin_pct": free_margin_pct,
        "danger": danger,
    }


def _show_account_metrics(account, risk):
    st.markdown("### Account Summary")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Balance", _fmt_money(risk["balance"]))
    c2.metric("Equity", _fmt_money(risk["equity"]))
    c3.metric("Free Margin", _fmt_money(risk["free_margin"]))
    c4.metric("Margin Level %", _fmt_percent(risk["margin_level"]))

    c5, c6, c7, c8 = st.columns(4)
    c5.metric("Used Margin", _fmt_money(risk["margin"]))
    c6.metric("Floating P/L", _fmt_money(risk["floating_pl"]))
    c7.metric("Drawdown %", _fmt_percent(risk["drawdown_pct"]))
    c8.metric("Risk Status", risk["danger"])

    if risk["danger"] in ["Extreme danger", "High danger"]:
        st.error(f"Account risk status: {risk['danger']}")
    elif risk["danger"] == "Medium":
        st.warning("Account risk status: Medium. Be careful with new entries.")
    elif risk["danger"] == "Healthy":
        st.success("Account risk status: Healthy by margin-level proxy.")
    else:
        st.info("Account risk status is unknown because margin level is missing.")


def _show_positions_metrics(positions):
    if positions.empty:
        return

    st.markdown("### Open Position Analysis")

    total_positions = len(positions)
    total_volume = positions["volume"].sum() if "volume" in positions.columns else 0
    total_profit = positions["profit"].sum() if "profit" in positions.columns else 0
    avg_pips = positions["pips"].mean() if "pips" in positions.columns else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Open Positions", total_positions)
    c2.metric("Total Lot", round(_safe_float(total_volume), 2))
    c3.metric("Total Floating P/L", round(_safe_float(total_profit), 2))
    c4.metric("Average Pips", round(_safe_float(avg_pips), 1))

    if "profit" in positions.columns:
        worst = positions.sort_values("profit").head(1).iloc[0]
        best = positions.sort_values("profit").tail(1).iloc[0]

        a, b, c = st.columns(3)
        a.metric("Worst Entry Profit", round(_safe_float(worst.get("profit")), 2))
        b.metric("Best Entry Profit", round(_safe_float(best.get("profit")), 2))

        if "symbol" in positions.columns:
            worst_symbol = worst.get("symbol", "N/A")
            c.metric("Worst Symbol", str(worst_symbol))
        else:
            c.metric("Worst Symbol", "N/A")


def _show_symbol_group_table(positions):
    if positions.empty or "symbol" not in positions.columns:
        return

    st.markdown("### Symbol Summary")

    agg_dict = {}

    if "profit" in positions.columns:
        agg_dict["profit"] = "sum"

    if "volume" in positions.columns:
        agg_dict["volume"] = "sum"

    if "pips" in positions.columns:
        agg_dict["pips"] = "mean"

    if not agg_dict:
        return

    symbol_df = positions.groupby("symbol").agg(agg_dict).reset_index()

    if "profit" in symbol_df.columns:
        symbol_df["profit"] = symbol_df["profit"].round(2)

    if "volume" in symbol_df.columns:
        symbol_df["volume"] = symbol_df["volume"].round(2)

    if "pips" in symbol_df.columns:
        symbol_df["pips"] = symbol_df["pips"].round(1)

    symbol_df["entries"] = positions.groupby("symbol").size().values

    st.dataframe(symbol_df, use_container_width=True)


def _show_blowout_wait_proxy(account, positions):
    """
    Simple danger proxy.
    This is NOT exact broker liquidation logic.
    It helps estimate how much floating loss space remains.
    """
    st.markdown("### Blow-Out Wait Proxy")

    equity = _safe_float(account.get("equity"))
    margin = _safe_float(account.get("margin"))
    free_margin = _safe_float(account.get("margin_free"))
    margin_level = _safe_float(account.get("margin_level"))

    if equity <= 0:
        st.error("Equity is zero or missing. Cannot calculate risk proxy.")
        return

    st.caption(
        "This is only a proxy. Real stop-out depends on broker rules, symbol margin, leverage, swap, commission, and spread."
    )

    stopout_level = st.number_input(
        "Broker stop-out level % proxy",
        min_value=1.0,
        max_value=500.0,
        value=50.0,
        step=5.0,
        help="Example: if broker stop-out is 50%, margin level below 50% can be dangerous."
    )

    if margin <= 0:
        st.info("No used margin detected, so blow-out proxy is not active.")
        return

    estimated_stopout_equity = margin * stopout_level / 100.0
    loss_room = equity - estimated_stopout_equity

    c1, c2, c3 = st.columns(3)
    c1.metric("Current Margin Level %", round(margin_level, 2))
    c2.metric("Estimated Stop-Out Equity", round(estimated_stopout_equity, 2))
    c3.metric("Approx Loss Room", round(loss_room, 2))

    if loss_room <= 0:
        st.error("Danger: equity is already near or below the stop-out proxy.")
    elif loss_room < equity * 0.1:
        st.warning("Warning: small loss room remains by this proxy.")
    else:
        st.success("Loss room exists by this proxy.")


def _show_lot_calculator(account):
    st.markdown("### 0.01 Lot Calculator")

    default_balance = _safe_float(account.get("margin_free"), 150.0)
    if default_balance <= 0:
        default_balance = 150.0

    balance = st.number_input(
        "Balance / free money",
        value=float(default_balance),
        min_value=0.0,
        step=10.0
    )

    money_per_001 = st.number_input(
        "Money reserved per 0.01 lot",
        value=150.0,
        min_value=1.0,
        step=10.0
    )

    max_001 = balance / max(money_per_001, 1.0)

    c1, c2, c3 = st.columns(3)
    c1.metric("Max 0.01-lot entries by rule", int(max_001))
    c2.metric("Max total lot by rule", round(int(max_001) * 0.01, 2))
    c3.metric("Money per 0.10 lot rule", round(money_per_001 * 10, 2))

    st.caption(
        "Example: if reserve is $150 per 0.01 lot, then 0.10 lot needs about $1500 free money by your rule."
    )


def _show_export_button(positions):
    if positions.empty:
        return

    csv = positions.to_csv(index=False).encode("utf-8")

    st.download_button(
        label="Download Open Positions CSV",
        data=csv,
        file_name=f"mt5_open_positions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv",
        use_container_width=True
    )


# ==========================================================
# MAIN STREAMLIT TAB
# ==========================================================

def show():
    st.markdown(
        """
        <div class="card">
            <div class="big-title">🏦 Doo Prime MT5 Account Reader</div>
            <div class="subtle">
                Reads account, margin, free margin, equity, open entries, profit/loss,
                pip calculation, hold time, symbol summary, 0.01 lot rule, and blow-out proxy.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    col_read, col_clear = st.columns([3, 1])

    with col_read:
        read_clicked = st.button(
            "Read Doo Prime MT5 Account",
            use_container_width=True
        )

    with col_clear:
        clear_clicked = st.button(
            "Clear",
            use_container_width=True
        )

    if clear_clicked:
        st.session_state.pop("mt5_account_snapshot", None)
        st.success("MT5 account snapshot cleared.")
        return

    if read_clicked:
        with st.spinner("Reading MT5 account..."):
            try:
                snap = get_mt5_account_snapshot()
            except Exception as e:
                snap = {
                    "ok": False,
                    "message": f"MT5 reader crashed: {e}",
                    "account": {},
                    "positions": []
                }

            st.session_state.mt5_account_snapshot = snap

            _safe_append_event(
                "account",
                {
                    "ok": snap.get("ok"),
                    "message": snap.get("message"),
                    "read_time": datetime.now().isoformat()
                }
            )

    snap = st.session_state.get("mt5_account_snapshot")

    if not snap:
        st.info(
            "Click the read button. This works on your Windows PC with MT5 installed and opened. "
            "On Streamlit Cloud, MT5 account reading may be unavailable, but the app will not crash."
        )
        return

    if not snap.get("ok"):
        st.error(snap.get("message", "MT5 account read failed."))
        with st.expander("Debug snapshot"):
            st.json(snap)
        return

    account = snap.get("account", {}) or {}
    raw_positions = snap.get("positions", []) or []

    positions = _positions_df(raw_positions)
    positions = _upgrade_positions_df(positions, account)

    risk = _account_risk_summary(account, positions)

    _show_account_metrics(account, risk)

    st.divider()

    if positions.empty:
        st.warning("No open positions.")
        _show_lot_calculator(account)
        return

    _show_positions_metrics(positions)

    st.markdown("### Open Entries")

    preferred_cols = [
        "ticket",
        "symbol",
        "side",
        "volume",
        "price_open",
        "price_current",
        "pips",
        "profit",
        "profit_pct_of_equity",
        "profit_per_0.01_lot",
        "hold_time",
        "time",
        "status",
        "comment",
        "magic",
    ]

    existing_cols = [c for c in preferred_cols if c in positions.columns]
    other_cols = [c for c in positions.columns if c not in existing_cols]

    display_df = positions[existing_cols + other_cols].copy()

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )

    _show_export_button(display_df)

    st.divider()

    _show_symbol_group_table(positions)

    st.divider()

    _show_blowout_wait_proxy(account, positions)

    st.divider()

    _show_lot_calculator(account)
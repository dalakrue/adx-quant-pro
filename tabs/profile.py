import streamlit as st, pandas as pd
from core.database import append_csv, read_csv
from core.common import log_event

GUIDE_TEXT = r'''
. Basic Understanding (The Foundation)

+DI = Bullish strength (Buying pressure)
-DI = Bearish strength (Selling pressure)
MADX (ADX) = Trend strength (How strong the move is, not direction)

Simple Rule:

If +DI > -DI → Market wants to go UP
If -DI > +DI → Market wants to go DOWN
Higher the difference = Stronger the direction


2. Core Indicators Explained (Easy Language)
IndicatorSimple MeaningGood ValueBad ValueWhat it tells youDSSMain direction power> 0 = Bullish
< -0 = BearishClose to 0Current momentum directionDSS AccelIs momentum speeding up?> 0 = Accelerating< 0 = SlowingVery important for entryCR (+DI/-DI Ratio)How dominant is the winning side> 2.0 = Strong< 1.5 = WeakDominance levelNS (Net Strength)Overall clarity of move> 0.35 = Clear< 0.25 = NoisyHow clean the trend isSTABHow stable the DI lines are< 6 = Stable> 10 = ChoppyNoise levelTCITrend Confidence Index> 1 = Strong< 0.5 = WeakCombined confidenceMOMQMomentum Quality> 0.5 = Good< 0.5 = PoorMomentum healthESIExhaustion Index< 80 = Healthy> 200 = ExhaustedRisk of reversal

3. Entry Rules (When to BUY or SELL)
Strong Entry Conditions (Best Setups)
You should see most of these together:

Direction Clear: DSS > 0 and DSS Accel > 0 → BUY
(or opposite for SELL)
Strong Dominance: CR > 2.0
Good Momentum: MOMQ > 0.5
Clean Move: NS > 0.35 and STAB < 6
High Confidence: TCI > 1.0
No Exhaustion: ESI < 80

Entry Score (from code) → Aim for 5 or more out of 8 filters.

4. Higher Timeframe Filters (Very Important)

MetricThresholdMeaningH4 Pressure> +8Strong bullish biasH4 Pressure< -8Strong bearish biasTrust Score≥ 78High quality setupTrust Score< 45AvoidVQS (Volatility Quality)≥ 68Good volatilityExhaustion> 55Danger - trend may endConflict Score> 45Mixed signals - risky
Golden Rule:
M1 signal must agree with H4 bias.
If H4 says BUY but M1 says SELL → Do not trade.

5. Exit & Hold Rules (Exit Survivability Engine)
Hold the trade if:

Survivability % > 75
Reversal Threat < 35
Decay Score is low
Position Quality Score (PQS) is high

Exit / Take Profit if:

Decay Score > 50
Reversal Threat > 50
Survivability < 55
Micro pressure goes against your trade
Exhaustion appears in higher timeframe

Emergency Exit Signals:

Liquidity Trap detected
Strong opposite micro pressure
MADX dropping fast
High Conflict + Decay

        # 📘 QUICK USER GUIDE

        # 🔹 What This Engine Does

        This engine analyzes:
        - Trend strength
        - Market momentum
        - Volatility
        - Reversal risk
        - Statistical edge
        - Market regime
        - ML-based direction probability

        It transforms raw market data into probability-based market states.

        ---

        # 🔹 Main Logic Flow

        Market Data
        ↓
        Indicators
        ↓
        Feature Engineering
        ↓
        Probability Models
        ↓
        Risk Engine
        ↓
        ML Confirmation
        ↓
        Regime Classification
        ↓
        Final Environment State

        ---

        # 🔹 Understanding the Main Metrics

        ## ADX

        Measures trend strength only.

        Important:
        ADX does NOT tell direction.

        Direction comes from:
        - +DI
        - -DI
        - Pressure

        Thresholds:
        - Below 20 → Weak trend
        - Above 25 → Strong trend
        - Above 30 → Powerful trend

        ---

        # 🔹 Pressure

        Equation:

        Pressure = +DI − -DI

        Purpose:
        Measures which side controls the market.

        Interpretation:
        - Positive → Bullish dominance
        - Negative → Bearish dominance
        - Near zero → Balance/chop

        ---

        # 🔹 ATR

        Measures volatility.

        High ATR:
        - Large price movement
        - Fast market

        Low ATR:
        - Small movement
        - Slow market

        Used for:
        - Dynamic SL/TP
        - Volatility normalization

        ---

        # 🔹 Trend Energy

        Equation:

        Trend Energy = ADX × ATR Pressure Ratio

        Purpose:
        Measures trend efficiency.

        High trend energy means:
        - Strong movement
        - Strong participation
        - Strong directional conviction

        ---

        # 🔹 Reversal Probability

        Purpose:
        Measures probability of market reversal.

        Built from:
        - DI crossover
        - ADX weakening
        - Weak pressure structure

        Interpretation:
        - Low → Stable trend
        - High → Unstable trend

        ---

        # 🔹 Continuation Probability

        Purpose:
        Measures probability that current trend continues.

        Uses:
        - ADX strength
        - Pressure dominance
        - Momentum acceleration

        High value:
        - Trend continuation more likely

        Low value:
        - Trend weakening

        ---

        # 🔹 Trade Quality

        Equation:

        Trade Quality =
        (Trend Energy × 0.6)
        + (Continuation × 0.3)
        − (Reversal × 0.4)

        Purpose:
        Measures overall setup quality.

        Higher score:
        - Better environment quality

        Lower score:
        - Poor environment

        ---

        # 🔹 Machine Learning Layer

        The ML model studies:
        - ADX
        - DI structure
        - ATR
        - Momentum
        - Pressure behavior

        Then predicts:
        Future direction after 5 candles.

        Output:
        - Direction prediction
        - Confidence probability

        ---

        # 🔹 Bayesian Win Probability

        Purpose:
        Estimate statistical edge using multiple probabilities.

        Combines:
        - Trend strength
        - Breakout strength
        - Chop conditions

        Interpretation:
        - High value → Better edge
        - Low value → Weak edge

        ---

        # 🔹 Conflict Score

        Purpose:
        Detect model disagreement.

        High conflict means:
        - Trend model disagrees with breakout model
        - Market structure unstable
        - Increased uncertainty

        Thresholds:
        - Below 20 → Stable
        - 20–40 → Mixed
        - Above 40 → Dangerous/unstable

        ---

        # 🔹 Risk Score

        Measures:
        - ML uncertainty
        - Conflict
        - Liquidity problems

        Higher risk score means:
        - Lower environment quality
        - Higher instability

        ---

        # 🔹 Tradeability Index

        Equation:

        Tradeability =
        Bayesian Win − (Conflict × 0.4)

        Purpose:
        Final market quality measurement.

        Interpretation:
        - High → Clean market structure
        - Medium → Selective conditions
        - Low → Weak/no edge

        ---

        # 🔹 Market Regimes

        ## Strong Trend
        Characteristics:
        - High ADX
        - Strong pressure
        - Positive acceleration

        Meaning:
        Market moving efficiently.

        ---

        ## Exhaustion
        Characteristics:
        - High ADX
        - Falling acceleration

        Meaning:
        Trend losing energy.

        ---

        ## Chop
        Characteristics:
        - Low pressure
        - Weak directional dominance

        Meaning:
        Sideways/noisy market.

        ---

        ## Reversal Risk
        Characteristics:
        - Weakening pressure
        - Directional instability

        Meaning:
        Possible structure transition.

        ---

        # 🔹 Why Multiple Models Are Used

        Single indicators fail frequently.

        This engine combines:
        - Trend analysis
        - Volatility analysis
        - Probability analysis
        - Regime analysis
        - Machine learning
        - Bayesian weighting

        Purpose:
        Reduce noise and improve environment filtering.

        ---

        # 🔹 Why Probability Matters

        Markets are uncertain.

        This engine does NOT predict certainty.

        It estimates:
        - Relative edge
        - Statistical probability
        - Market quality
        - Structural stability

        The goal is:
        Improve decision quality, not predict perfectly.

        ---

        # 🔹 System Philosophy

        Main principles:
        - Probability over prediction
        - Structure over emotion
        - Risk-adjusted analysis
        - Regime-aware filtering
        - Multi-layer confirmation

        The engine focuses on:
        - Detecting favorable environments
        - Avoiding unstable conditions
        - Measuring structural quality
        - Quantifying uncertainty
        1. Market is always a 2-force system: BUYERS vs SELLERS<br>
        2. +DI represents buyer pressure<br>
        3. -DI represents seller pressure<br>
        4. Price direction = dominance of stronger side<br><br>

        5. When +DI > -DI → bullish structure forms<br>
        6. When -DI > +DI → bearish structure forms<br><br>

        7. MADX measures strength of trend expansion<br>
        8. High MADX = strong directional continuation<br>
        9. Low MADX = consolidation / fake movement<br><br>

        10. DSS measures directional strength stability<br>
        11. Positive DSS = controlled bullish flow<br>
        12. Negative DSS = controlled bearish flow<br><br>

        13. Your system is NOT prediction based<br>
        14. It is STRUCTURE CONFIRMATION based<br>
        15. It avoids random market noise<br><br>

        16. Key idea: trade only when structure aligns across timeframes<br>
        17. M1 = execution layer<br>
        18. H4 = institutional direction layer<br>
        19. Alignment between layers = high probability setup<br><br>

        20. If M1 disagrees with H4 → avoid trade<br>
        21. If both align → continuation probability increases<br>




        1. TCI = Trend Confidence Index<br>
        → measures structural confidence of trend continuation<br><br>

        2. MOMQ = Momentum Quality<br>
        → detects acceleration or weakening momentum<br><br>

        3. CR = Control Ratio<br>
        → dominance strength between buyers and sellers<br><br>

        4. DSS = Direction Strength Stability<br>
        → prevents fake spike entries<br><br>

        5. High TCI + High MOMQ = strong trend phase<br>
        6. Low TCI = unstable market = no trade zone<br><br>

        7. MOMQ rising = trend acceleration phase<br>
        8. MOMQ falling = exhaustion phase<br><br>

        9. CR > 2 = strong dominance condition<br>
        10. CR < 1 = weak/no control zone<br><br>

        11. Your system filters low-quality volatility<br>
        12. It only accepts structured movement<br>




        STEP 1: Check H4 direction<br>
        STEP 2: Check M1 direction<br>
        STEP 3: Confirm alignment<br><br>

        STEP 4: Validate TCI > 1<br>
        STEP 5: Validate MOMQ > 0.5<br>
        STEP 6: Confirm DSS positive trend<br><br>

        ENTRY RULES:<br>
        - Only enter when ALL conditions align<br>
        - Avoid mixed signals<br>
        - Avoid low MADX environment<br><br>

        INVALID SETUPS:<br>
        - M1 opposite H4<br>
        - MOMQ dropping<br>
        - DSS unstable<br>





        FILTER 1: Trend Strength Filter (TCI)<br>
        FILTER 2: Momentum Filter (MOMQ)<br>
        FILTER 3: Control Filter (CR)<br>
        FILTER 4: Stability Filter (DSS)<br><br>

        PURPOSE:<br>
        → Remove fake breakouts<br>
        → Remove news spikes<br>
        → Remove low probability trades<br><br>

        RESULT INTERPRETATION:<br>
        - ALL filters aligned = HIGH probability<br>
        - 2 filters missing = WARNING<br>
        - 3+ filters missing = NO TRADE<br>


# 📘 Restored Original Guide + Quant Upgrade

## Basic Understanding
+DI = Bullish strength / buying pressure.
-DI = Bearish strength / selling pressure.
MADX / ADX = trend strength, not direction.

If +DI > -DI, market wants to go up. If -DI > +DI, market wants to go down. The bigger the difference, the stronger the direction.

## Core Indicators
DSS = Direction Strength Stability. Positive DSS supports BUY, negative DSS supports SELL.
DSS Accel = whether momentum is speeding up or slowing down.
CR = Control Ratio, +DI divided by -DI. Above 2.0 means stronger dominance.
NS = Net Strength. Above 0.35 means cleaner trend.
STAB = line stability. Lower is cleaner.
TCI = Trend Confidence Index. Higher means stronger trend confidence.
MOMQ = Momentum Quality. Rising means better momentum health.
ESI = Exhaustion Index. Too high means reversal/exhaustion risk.

## Entry Logic
Best setup usually needs: clear DSS direction, DSS acceleration, CR > 2, MOMQ > 0.5, NS > 0.35, STAB < 6, TCI > 1, and no exhaustion. M1 should agree with H4. If M1 and H4 disagree, avoid or reduce risk.

## Exit / Hold Logic
Hold when survivability is high, reversal threat is low, decay score is low, and PQS is high. Exit or scale out when decay score rises, reversal threat rises, micro pressure goes against your trade, or exhaustion appears on higher timeframe.

## Why Advanced History Matching Matters
The system compares current ADX, DI pressure, ATR, volatility, wick/body behavior, momentum, and regime features against previous days and times. The most similar day/time table helps you adjust strategy based on what usually happened after similar market conditions.



## Last-120 Similar Day Ranking Upgrade
The upgraded backtest matcher now compares **today's latest 120 candles** against candidate 120-candle windows from the **last 60 days**. It intentionally excludes **today and yesterday**, so the result is not biased by the same live session or yesterday's very recent structure.

Ranking uses ADX, +DI, -DI, ATR, pressure, ADX slope, returns, wick/body behavior, volatility regime, trend power, momentum velocity, range expansion, fat-tail risk, and mean-distance features. The table shows which historical day/time is most similar, the similarity percentage, future move after the selected horizon, and whether that historical pattern became bullish or bearish.

Priority use: when the top similar windows agree with the ML bias, the bias is safer. When they conflict, reduce lot size, wait, or use partial entry only.

## System Philosophy
Probability over prediction. Structure over emotion. Risk-adjusted analysis. Regime-aware filtering. Use the app to reduce bad trades, not to guarantee any trade.
'''
def _safe_df(name):
    try:
        df = read_csv(name)
        if df is None:
            return pd.DataFrame()
        return df
    except Exception as e:
        st.warning(f"Could not load {name}: {e}")
        return pd.DataFrame()


def _safe_append(name, row):
    try:
        append_csv(name, row)
        return True
    except Exception as e:
        st.error(f"Could not save to {name}: {e}")
        return False


def _safe_log(msg):
    try:
        log_event(msg)
    except Exception:
        st.session_state.setdefault("activity_log", [])
        st.session_state.activity_log.insert(
            0,
            {"time": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"), "event": msg}
        )


def _init_profile_state():
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


def _profile_css():
    st.markdown(
        """
        <style>
        .profile-card {
            background: linear-gradient(135deg, rgba(235,247,255,.92), rgba(245,248,252,.88));
            border: 1px solid rgba(120,170,210,.35);
            border-radius: 22px;
            padding: 18px;
            box-shadow: 0 10px 30px rgba(30, 90, 130, .12);
            margin-bottom: 16px;
        }
        .mini-title {
            font-size: 14px;
            opacity: .72;
            font-weight: 700;
            margin-bottom: 4px;
        }
        .big-value {
            font-size: 26px;
            font-weight: 900;
        }
        .status-good {
            color: #087f5b;
            font-weight: 800;
        }
        .status-warn {
            color: #b7791f;
            font-weight: 800;
        }
        .status-bad {
            color: #c92a2a;
            font-weight: 800;
        }
        @media (max-width: 768px) {
            .profile-card {
                padding: 10px;
                border-radius: 14px;
                font-size: 12px;
            }
            .big-value {
                font-size: 18px;
            }
            div[data-testid="stMetricValue"] {
                font-size: 18px;
            }
            div[data-testid="stMetricLabel"] {
                font-size: 11px;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _download_button(df, label, filename):
    if df is not None and not df.empty:
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label=label,
            data=csv,
            file_name=filename,
            mime="text/csv",
            use_container_width=True,
        )


def _data_health_box(name, df):
    rows = 0 if df is None else len(df)
    cols = 0 if df is None or df.empty else len(df.columns)

    if rows == 0:
        status = "EMPTY"
        cls = "status-warn"
    elif rows < 20:
        status = "LOW DATA"
        cls = "status-warn"
    else:
        status = "READY"
        cls = "status-good"

    st.markdown(
        f"""
        <div class="profile-card">
            <div class="mini-title">{name}</div>
            <div class="big-value">{rows} rows / {cols} cols</div>
            <div class="{cls}">{status}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _filter_df(df, search_text=""):
    if df is None or df.empty:
        return pd.DataFrame()

    out = df.copy()

    if search_text.strip():
        s = search_text.strip().lower()
        mask = out.astype(str).apply(
            lambda col: col.str.lower().str.contains(s, na=False)
        ).any(axis=1)
        out = out[mask]

    return out


def show():
    _init_profile_state()
    _profile_css()

    st.markdown("# 👤 Quant Profile Dashboard")

    tabs = st.tabs([
        "📄 Overview",
        "🧠 Market Core Logic",
        "📘 Guide",
        "📝 Saved Notes Viewer",
        "✏️ Edit Profile",
        "📊 Trade History",
        "⚙️ Settings",
        "📘 Activity Log",
        "🧪 Train Data",
        "🧰 System Health",
    ])

    # =========================
    # TAB 0 — OVERVIEW
    # =========================
    with tabs[0]:
        st.markdown('<div class="profile-card">', unsafe_allow_html=True)
        st.subheader("Trading Intelligence Overview")

        history = _safe_df("backtest_results")
        timer = _safe_df("timer_history")
        saved_notes = _safe_df("saved_notes")

        c = st.columns(4)
        c[0].metric("Saved Backtests", len(history))
        c[1].metric("Timer Records", len(timer))
        c[2].metric("Saved Notes", len(saved_notes) if not saved_notes.empty else len(st.session_state.get("notes", [])))
        c[3].metric("Activity Logs", len(st.session_state.get("activity_log", [])))

        st.divider()

        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown("### 👤 Profile")
            st.write("Name:", st.session_state.get("profile_name", "Quant Trader"))
            st.write("Goal:", st.session_state.get("profile_goal", "12H Hold Strategy"))
        with c2:
            st.markdown("### ⚙️ Engine")
            st.write("Auto Entry:", "ON" if st.session_state.get("setting_auto_entry") else "OFF")
            st.write("Exit Alerts:", "ON" if st.session_state.get("setting_exit_alerts") else "OFF")
            st.write("Risk Engine:", "ON" if st.session_state.get("setting_risk_active") else "OFF")
        with c3:
            st.markdown("### 📱 UI")
            st.write("Phone Mode:", "ON" if st.session_state.get("phone_mode") else "OFF")
            st.write("Risk Mode:", st.session_state.get("risk_mode", "Balanced"))

        if not history.empty:
            st.markdown("### Latest Backtest Results")
            st.dataframe(history.tail(15), use_container_width=True)
            _download_button(history, "⬇️ Download Backtest CSV", "backtest_results.csv")
        else:
            st.info("No backtest results saved yet.")

        st.markdown("</div>", unsafe_allow_html=True)

    # =========================
    # TAB 1 — MARKET CORE LOGIC
    # =========================
    with tabs[1]:
        st.markdown('<div class="profile-card">', unsafe_allow_html=True)
        st.markdown(GUIDE_TEXT)
        st.info("This guide keeps the original reading material and adds the upgraded ML/history-matching explanation.")
        st.markdown("</div>", unsafe_allow_html=True)

    # =========================
    # TAB 2 — GUIDE
    # =========================
    with tabs[2]:
        st.markdown('<div class="profile-card">', unsafe_allow_html=True)

        search_guide = st.text_input("Search guide text", key="guide_search")

        if search_guide.strip():
            parts = GUIDE_TEXT.splitlines()
            matches = [line for line in parts if search_guide.lower() in line.lower()]
            st.success(f"Found {len(matches)} matching lines")
            for line in matches[:100]:
                st.markdown(f"- {line}")
        else:
            st.markdown(GUIDE_TEXT)

        st.markdown("</div>", unsafe_allow_html=True)

    # =========================
    # TAB 3 — SAVED NOTES
    # =========================
    with tabs[3]:
        st.subheader("Saved Notes")

        note = st.text_area("Write / edit note", key="profile_note_text", height=160)

        c1, c2, c3 = st.columns(3)

        with c1:
            if st.button("💾 Save Note", key="save_note", use_container_width=True):
                if note.strip():
                    row = {
                        "time": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "note": note.strip()
                    }
                    st.session_state.notes.insert(0, row)
                    _safe_append("saved_notes", row)
                    _safe_log("Saved profile note")
                    st.success("Note saved")
                    st.rerun()
                else:
                    st.warning("Write a note first.")

        with c2:
            if st.button("🧹 Clear Text Box", key="clear_note_box", use_container_width=True):
                st.session_state.profile_note_text = ""
                st.rerun()

        with c3:
            if st.button("🗑️ Delete Session Notes", key="delete_notes", use_container_width=True):
                st.session_state.notes = []
                _safe_log("Deleted session notes")
                st.success("Session notes deleted")
                st.rerun()

        saved = _safe_df("saved_notes")

        note_search = st.text_input("Search saved notes", key="note_search")
        filtered_notes = _filter_df(saved, note_search)

        if not filtered_notes.empty:
            st.dataframe(filtered_notes.tail(100), use_container_width=True)
            _download_button(filtered_notes, "⬇️ Download Notes CSV", "saved_notes.csv")
        else:
            st.info("No saved notes found.")

        if st.session_state.get("notes"):
            st.markdown("### Session Notes")
            for i, n in enumerate(st.session_state.get("notes", [])):
                with st.expander(f"{n.get('time', 'unknown')} — note {i+1}"):
                    st.write(n.get("note", ""))

    # =========================
    # TAB 4 — EDIT PROFILE
    # =========================
    with tabs[4]:
        st.subheader("Edit Profile")

        name = st.text_input(
            "Profile name",
            value=st.session_state.get("profile_name", "Quant Trader"),
            key="edit_profile_name"
        )

        style = st.selectbox(
            "Trading style",
            ["12H Hold", "NY Session", "London Out", "Scalp", "Swing"],
            key="edit_profile_style"
        )

        goal = st.text_input(
            "Main trading goal",
            value=st.session_state.get("profile_goal", "12H Hold Strategy"),
            key="edit_profile_goal"
        )

        risk_mode = st.selectbox(
            "Risk mode",
            ["Conservative", "Balanced", "Aggressive"],
            index=["Conservative", "Balanced", "Aggressive"].index(
                st.session_state.get("risk_mode", "Balanced")
            ),
            key="edit_risk_mode"
        )

        if st.button("✅ Update Profile", key="update_profile", use_container_width=True):
            st.session_state.profile_name = name
            st.session_state.profile_goal = goal
            st.session_state.risk_mode = risk_mode

            row = {
                "time": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
                "name": name,
                "style": style,
                "goal": goal,
                "risk_mode": risk_mode
            }

            _safe_append("profile_changes", row)
            _safe_log("Updated profile")
            st.success("Profile updated")

    # =========================
    # TAB 5 — TRADE HISTORY
    # =========================
    with tabs[5]:
        st.subheader("Trade / System History")

        history_names = [
            "engine_mix_snapshots",
            "prelive_snapshots",
            "pre_manual_runs",
            "risk_snapshots",
            "doo_prime_account_history",
            "backtest_results",
            "timer_history",
            "profile_changes",
            "saved_notes",
        ]

        history_search = st.text_input("Search all history tables", key="history_search")

        for name in history_names:
            df = _safe_df(name)
            with st.expander(f"{name} — {len(df)} rows"):
                filtered = _filter_df(df, history_search)
                if filtered.empty:
                    st.info("No data found.")
                else:
                    st.dataframe(filtered.tail(300), use_container_width=True)
                    _download_button(filtered, f"⬇️ Download {name}", f"{name}.csv")

    # =========================
    # TAB 6 — SETTINGS
    # =========================
    with tabs[6]:
        st.subheader("System Settings")

        st.session_state.setting_auto_entry = st.toggle(
            "Auto Entry Engine",
            value=st.session_state.get("setting_auto_entry", True),
            key="toggle_auto_entry"
        )

        st.session_state.setting_exit_alerts = st.toggle(
            "Exit Engine Alerts",
            value=st.session_state.get("setting_exit_alerts", True),
            key="toggle_exit_alerts"
        )

        st.session_state.setting_risk_active = st.toggle(
            "Risk Engine Active",
            value=st.session_state.get("setting_risk_active", True),
            key="toggle_risk_active"
        )

        st.session_state.setting_phone_mode = st.toggle(
            "Ocean glass mobile compact mode",
            value=st.session_state.get("phone_mode", False),
            key="toggle_phone_mode"
        )

        st.session_state.phone_mode = st.session_state.setting_phone_mode

        st.info("Settings are stored safely in session_state and will not break original modules.")

        if st.button("💾 Save Settings Snapshot", key="save_settings_snapshot", use_container_width=True):
            row = {
                "time": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
                "auto_entry": st.session_state.setting_auto_entry,
                "exit_alerts": st.session_state.setting_exit_alerts,
                "risk_active": st.session_state.setting_risk_active,
                "phone_mode": st.session_state.phone_mode,
                "risk_mode": st.session_state.get("risk_mode", "Balanced")
            }
            _safe_append("settings_history", row)
            _safe_log("Saved settings snapshot")
            st.success("Settings snapshot saved")

    # =========================
    # TAB 7 — ACTIVITY LOG
    # =========================
    with tabs[7]:
        st.subheader("Activity Log")

        logs = pd.DataFrame(st.session_state.get("activity_log", []))

        if logs.empty:
            saved_logs = _safe_df("activity_log")
            if not saved_logs.empty:
                logs = saved_logs

        if logs.empty:
            st.info("No activity logs yet.")
        else:
            st.dataframe(logs, use_container_width=True)
            _download_button(logs, "⬇️ Download Activity Log", "activity_log.csv")

        if st.button("🧹 Clear Session Activity Log", key="clear_activity_log", use_container_width=True):
            st.session_state.activity_log = []
            st.success("Session activity log cleared")
            st.rerun()

    # =========================
    # TAB 8 — TRAIN DATA
    # =========================
    with tabs[8]:
        st.subheader("Train Data From Exited/Saved Results")

        df = _safe_df("backtest_results")

        if df.empty:
            st.warning("No saved backtest results yet.")
        else:
            st.dataframe(df.tail(200), use_container_width=True)

            c1, c2 = st.columns(2)

            with c1:
                train_rows = st.number_input(
                    "Rows to load into training memory",
                    min_value=50,
                    max_value=5000,
                    value=min(500, max(50, len(df))),
                    step=50,
                    key="train_rows_count"
                )

            with c2:
                st.metric("Available Rows", len(df))

            if st.button("🧪 Train Memory From Saved Results", key="train_saved", use_container_width=True):
                selected = df.tail(int(train_rows))
                st.session_state.training_rows = selected.to_dict("records")
                _safe_log(f"Loaded {len(selected)} rows into training memory")
                st.success(f"Loaded {len(selected)} rows into training memory")

            if st.session_state.get("training_rows"):
                st.success(f"Training memory active: {len(st.session_state.training_rows)} rows")

    # =========================
    # TAB 9 — SYSTEM HEALTH
    # =========================
    with tabs[9]:
        st.subheader("System Health Check")

        check_files = [
            "backtest_results",
            "timer_history",
            "saved_notes",
            "profile_changes",
            "settings_history",
            "engine_mix_snapshots",
            "prelive_snapshots",
            "risk_snapshots",
        ]

        cols = st.columns(2)

        for i, name in enumerate(check_files):
            df = _safe_df(name)
            with cols[i % 2]:
                _data_health_box(name, df)

        st.divider()

        st.markdown("### Session State Keys")
        ss = pd.DataFrame(
            [{"key": k, "type": type(v).__name__, "preview": str(v)[:120]} for k, v in st.session_state.items()]
        )

        st.dataframe(ss, use_container_width=True)

        _download_button(ss, "⬇️ Download Session State Preview", "session_state_preview.csv")
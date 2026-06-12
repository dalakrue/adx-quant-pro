"""Lightweight persistent login/guest/OTP gate for New7 Streamlit app.

This module is intentionally small and CPU-light. It stores accounts outside the
code folder by default (~/.new7_quant_app/auth.sqlite3) so app updates do not
remove accounts. Gmail OTP is sent only when SMTP credentials are configured;
otherwise a local developer OTP is shown so the UI remains testable without
crashing.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import secrets
import smtplib
import sqlite3
import time
from email.message import EmailMessage
from pathlib import Path
from typing import Dict, Tuple

import streamlit as st

UNIQUE = "20260612_real_auth"


def _db_path() -> Path:
    env = os.environ.get("NEW7_AUTH_DB", "").strip()
    if env:
        return Path(env).expanduser()
    return Path.home() / ".new7_quant_app" / "auth.sqlite3"


def _connect() -> sqlite3.Connection:
    path = _db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(path), timeout=8)
    con.execute("PRAGMA journal_mode=WAL")
    con.execute(
        "CREATE TABLE IF NOT EXISTS users (email TEXT PRIMARY KEY, password_hash TEXT NOT NULL, salt TEXT NOT NULL, created_at REAL NOT NULL)"
    )
    con.execute(
        "CREATE TABLE IF NOT EXISTS otps (email TEXT NOT NULL, code_hash TEXT NOT NULL, expires_at REAL NOT NULL, created_at REAL NOT NULL, consumed INTEGER DEFAULT 0)"
    )
    con.execute(
        "CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL)"
    )
    con.commit()
    return con


def _hash_password(password: str, salt: bytes | None = None) -> Tuple[str, str]:
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", str(password).encode("utf-8"), salt, 120_000)
    return base64.b64encode(digest).decode("ascii"), base64.b64encode(salt).decode("ascii")


def _verify_password(password: str, digest_b64: str, salt_b64: str) -> bool:
    try:
        calc, _ = _hash_password(password, base64.b64decode(salt_b64.encode("ascii")))
        return secrets.compare_digest(calc, digest_b64)
    except Exception:
        return False


def _set_setting(key: str, value: str) -> None:
    with _connect() as con:
        con.execute("INSERT OR REPLACE INTO settings(key,value) VALUES(?,?)", (key, value))
        con.commit()


def _get_setting(key: str, default: str = "") -> str:
    try:
        with _connect() as con:
            row = con.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
            return str(row[0]) if row else default
    except Exception:
        return default


def _create_user(email: str, password: str) -> None:
    digest, salt = _hash_password(password)
    with _connect() as con:
        con.execute(
            "INSERT OR REPLACE INTO users(email,password_hash,salt,created_at) VALUES(?,?,?,?)",
            (email.lower().strip(), digest, salt, time.time()),
        )
        con.commit()


def _check_user(email: str, password: str) -> bool:
    try:
        with _connect() as con:
            row = con.execute("SELECT password_hash,salt FROM users WHERE email=?", (email.lower().strip(),)).fetchone()
        return bool(row and _verify_password(password, str(row[0]), str(row[1])))
    except Exception:
        return False


def _store_otp(email: str, code: str) -> None:
    digest = hashlib.sha256((email.lower().strip() + ":" + code).encode("utf-8")).hexdigest()
    with _connect() as con:
        con.execute("DELETE FROM otps WHERE email=?", (email.lower().strip(),))
        con.execute(
            "INSERT INTO otps(email,code_hash,expires_at,created_at,consumed) VALUES(?,?,?,?,0)",
            (email.lower().strip(), digest, time.time() + 10 * 60, time.time()),
        )
        con.commit()


def _verify_otp(email: str, code: str) -> bool:
    digest = hashlib.sha256((email.lower().strip() + ":" + str(code).strip()).encode("utf-8")).hexdigest()
    with _connect() as con:
        row = con.execute(
            "SELECT rowid,code_hash,expires_at,consumed FROM otps WHERE email=? ORDER BY created_at DESC LIMIT 1",
            (email.lower().strip(),),
        ).fetchone()
        if not row:
            return False
        rowid, stored, expires, consumed = row
        ok = (not int(consumed or 0)) and time.time() <= float(expires or 0) and secrets.compare_digest(str(stored), digest)
        if ok:
            con.execute("UPDATE otps SET consumed=1 WHERE rowid=?", (rowid,))
            con.commit()
        return bool(ok)


def _smtp_cfg_from_env_or_db() -> Dict[str, str]:
    return {
        "host": os.environ.get("NEW7_SMTP_HOST") or _get_setting("smtp_host", "smtp.gmail.com"),
        "port": os.environ.get("NEW7_SMTP_PORT") or _get_setting("smtp_port", "587"),
        "email": os.environ.get("NEW7_SMTP_EMAIL") or _get_setting("smtp_email", ""),
        "password": os.environ.get("NEW7_SMTP_PASSWORD") or _get_setting("smtp_password", ""),
    }


def _send_otp_email(to_email: str, code: str) -> Tuple[bool, str]:
    cfg = _smtp_cfg_from_env_or_db()
    sender = cfg.get("email", "").strip()
    password = cfg.get("password", "").strip()
    if not sender or not password:
        return False, "SMTP Gmail sender/app-password not configured. OTP is shown locally for testing."
    try:
        msg = EmailMessage()
        msg["From"] = sender
        msg["To"] = to_email
        msg["Subject"] = "Your New7 Quant App OTP"
        msg.set_content(f"Your New7 Quant App verification code is: {code}\n\nThis code expires in 10 minutes.")
        with smtplib.SMTP(cfg.get("host") or "smtp.gmail.com", int(cfg.get("port") or 587), timeout=12) as smtp:
            smtp.starttls()
            smtp.login(sender, password)
            smtp.send_message(msg)
        return True, f"OTP sent to {to_email}."
    except Exception as exc:
        return False, f"OTP email failed: {str(exc)[:160]}. OTP is shown locally for testing."


def _auth_css() -> None:
    st.markdown(
        """
        <style>
        .new7-auth-shell{max-width:920px;margin:4vh auto 0 auto;padding:22px;border-radius:30px;
            background:linear-gradient(140deg,rgba(236,254,255,.92),rgba(255,255,255,.74));
            border:1px solid rgba(14,165,233,.22);box-shadow:0 30px 80px rgba(15,23,42,.14)}
        .new7-auth-title{font-size:2.2rem;font-weight:950;letter-spacing:-.04em;margin-bottom:.2rem;color:#0f172a}
        .new7-auth-sub{color:#475569;font-weight:650;margin-bottom:1rem}
        .stButton>button{border-radius:999px!important;min-height:48px!important;font-weight:900!important}
        @media(max-width:780px){.new7-auth-shell{margin:.25rem;padding:14px;border-radius:22px}.new7-auth-title{font-size:1.55rem}}
        </style>
        """,
        unsafe_allow_html=True,
    )


def _login_success(email: str, guest: bool = False) -> None:
    st.session_state["new7_auth_logged_in"] = True
    st.session_state["new7_auth_guest"] = bool(guest)
    st.session_state["new7_auth_email"] = email


def render_auth_gate() -> bool:
    """Return True when the app should continue, False when login page is shown."""
    if st.session_state.get("new7_auth_logged_in"):
        return True
    _connect()  # ensure persistent database exists before UI actions
    _auth_css()
    st.markdown('<div class="new7-auth-shell">', unsafe_allow_html=True)
    st.markdown('<div class="new7-auth-title">⚡ New7 Quant App</div>', unsafe_allow_html=True)
    st.markdown('<div class="new7-auth-sub">Login, create account with OTP, or continue as Guest. Accounts are stored in a persistent SQLite database.</div>', unsafe_allow_html=True)

    mode = st.radio("Open mode", ["Login", "Create Account", "Guest"], horizontal=True, key=f"auth_mode_{UNIQUE}")

    if mode == "Guest":
        st.info("Guest mode opens the app without saving an account.")
        if st.button("🚀 Continue as Guest", use_container_width=True, key=f"guest_{UNIQUE}"):
            _login_success("Guest", guest=True)
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
        return False

    if mode == "Login":
        c1, c2 = st.columns(2)
        email = c1.text_input("Email", key=f"login_email_{UNIQUE}", placeholder="your@gmail.com")
        password = c2.text_input("Password", type="password", key=f"login_pwd_{UNIQUE}")
        b1, b2 = st.columns([1, 1])
        if b1.button("🔐 Login", use_container_width=True, key=f"login_btn_{UNIQUE}"):
            if _check_user(email, password):
                _login_success(email, guest=False)
                st.success("Login successful.")
                st.rerun()
            else:
                st.error("Wrong email/password, or account not created yet.")
        if b2.button("🚀 Guest", use_container_width=True, key=f"login_guest_btn_{UNIQUE}"):
            _login_success("Guest", guest=True)
            st.rerun()
        st.caption(f"Account DB: {_db_path()}")
        st.markdown("</div>", unsafe_allow_html=True)
        return False

    # Create account + OTP
    st.markdown("#### ✉️ Create account with OTP")
    c1, c2 = st.columns(2)
    email = c1.text_input("Gmail / Email", key=f"create_email_{UNIQUE}", placeholder="your@gmail.com")
    password = c2.text_input("New password", type="password", key=f"create_pwd_{UNIQUE}")
    with st.expander("Open / Close — Gmail SMTP sender setup for real OTP email", expanded=False):
        st.caption("To really receive OTP in Gmail, enter a Gmail sender address and Gmail App Password. It is saved in the persistent auth database. Without this, the OTP is displayed locally for testing.")
        host = st.text_input("SMTP host", value=_get_setting("smtp_host", "smtp.gmail.com"), key=f"smtp_host_{UNIQUE}")
        port = st.text_input("SMTP port", value=_get_setting("smtp_port", "587"), key=f"smtp_port_{UNIQUE}")
        sender = st.text_input("Sender Gmail", value=_get_setting("smtp_email", ""), key=f"smtp_email_{UNIQUE}")
        sender_pwd = st.text_input("Sender Gmail App Password", type="password", value=_get_setting("smtp_password", ""), key=f"smtp_pwd_{UNIQUE}")
        if st.button("💾 Save SMTP settings", use_container_width=True, key=f"save_smtp_{UNIQUE}"):
            _set_setting("smtp_host", host.strip() or "smtp.gmail.com")
            _set_setting("smtp_port", port.strip() or "587")
            _set_setting("smtp_email", sender.strip())
            _set_setting("smtp_password", sender_pwd.strip())
            st.success("SMTP settings saved in persistent auth database.")
    c3, c4 = st.columns(2)
    if c3.button("📨 Send OTP", use_container_width=True, key=f"send_otp_{UNIQUE}"):
        if not email or "@" not in email or not password:
            st.error("Enter a valid email and password first.")
        else:
            code = f"{secrets.randbelow(900000) + 100000}"
            _store_otp(email, code)
            st.session_state[f"last_local_otp_{UNIQUE}"] = code
            ok, msg = _send_otp_email(email, code)
            if ok:
                st.success(msg)
            else:
                st.warning(msg)
                st.code(code, language="text")
    otp = c4.text_input("OTP code", key=f"otp_code_{UNIQUE}", max_chars=6)
    if st.button("✅ Verify OTP + Create Account", use_container_width=True, key=f"verify_create_{UNIQUE}"):
        if _verify_otp(email, otp):
            _create_user(email, password)
            _login_success(email, guest=False)
            st.success("Account created and logged in.")
            st.rerun()
        else:
            st.error("OTP invalid or expired. Send a new OTP.")
    st.caption(f"Persistent DB: {_db_path()}")
    st.markdown("</div>", unsafe_allow_html=True)
    return False


def render_auth_status_sidebar() -> None:
    try:
        with st.sidebar.expander("🔐 Login / Logout", expanded=False):
            user = st.session_state.get("new7_auth_email", "Guest")
            st.caption(f"Signed in as: {user}")
            st.caption("Guest mode" if st.session_state.get("new7_auth_guest") else "Account mode")
            if st.button("🚪 Logout", use_container_width=True, key=f"sidebar_logout_{UNIQUE}"):
                st.session_state["new7_auth_logged_in"] = False
                st.session_state["new7_auth_guest"] = False
                st.session_state["new7_auth_email"] = ""
                st.rerun()
    except Exception:
        pass

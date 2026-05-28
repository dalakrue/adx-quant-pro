import streamlit as st
try:
    from streamlit_autorefresh import st_autorefresh
except Exception:
    def st_autorefresh(*args, **kwargs):
        return None
from core.common import init_state
from core.styles import apply_global_styles, auto_close_sidebar_script
from core.navigation import sidebar_nav
from core.data_connectors import maybe_refresh

def run_app():
    st.set_page_config(page_title='M1 ADX Quant Pro', page_icon='⚡', layout='wide', initial_sidebar_state='expanded')
    init_state(); apply_global_styles(st.session_state.get('phone_mode',False)); auto_close_sidebar_script()
    st_autorefresh(interval=600000, key='ten_min_refresh')
    maybe_refresh(st.session_state.get('symbol','XAUUSD'), st.session_state.get('twelve_api_key',''), 600)
    tab=sidebar_nav()
    if tab=='Home':
        from tabs.home import show
    elif tab=='Engine':
        from tabs.engine import show
    elif tab=='Backtest':
        from tabs.backtest import show
    elif tab=='Pre Original':
        from tabs.pre_original import show
    elif tab=='Backtest Original':
        from tabs.backtest_original import show
    elif tab=='Prelive':
        from tabs.prelive import show
    else:
        from tabs.profile import show
    show()

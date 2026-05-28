import streamlit as st


def apply_global_styles(phone_mode: bool = False):
    maxw = "430px" if phone_mode else "1180px"
    pad = "0.45rem" if phone_mode else "0.85rem 1.20rem"
    font = "10.5px" if phone_mode else "11.5px"
    h1 = "1.05rem" if phone_mode else "1.35rem"
    h2 = "0.95rem" if phone_mode else "1.12rem"
    h3 = "0.86rem" if phone_mode else "0.98rem"
    btn_h = "34px" if phone_mode else "38px"
    metric_v = "16px" if phone_mode else "19px"
    tab_font = "9.5px" if phone_mode else "10.5px"
    card_pad = "8px" if phone_mode else "11px"
    radius = "14px" if phone_mode else "18px"

    st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

:root {{
  --glass: rgba(255,255,255,.78);
  --glass2: rgba(240,249,255,.64);
  --line: rgba(14,116,144,.16);
  --txt:#0f172a;
  --muted:#075985;
  --blue:#38bdf8;
}}

html, body, [class*="css"] {{
  font-family: Inter, sans-serif !important;
  color: var(--txt) !important;
  font-size:{font}!important;
}}

.stApp {{
  background:
    radial-gradient(circle at top left, rgba(224,242,254,.68), transparent 30%),
    radial-gradient(circle at top right, rgba(219,234,254,.55), transparent 34%),
    radial-gradient(circle at bottom right, rgba(240,249,255,.85), transparent 38%),
    linear-gradient(135deg,#f8fbff 0%,#eef8ff 45%,#f8fafc 100%) !important;
  background-attachment: fixed;
}}

.main .block-container {{
  max-width:{maxw}!important;
  width:100%!important;
  padding:{pad}!important;
  margin-left:auto!important;
  margin-right:auto!important;
}}

section[data-testid="stSidebar"] {{
  background: rgba(248,252,255,.78)!important;
  backdrop-filter: blur(26px) saturate(170%)!important;
  border-right:1px solid rgba(14,116,144,.14)!important;
}}

section[data-testid="stSidebar"] * {{
  font-size:{font}!important;
}}

h1 {{
  font-size:{h1}!important;
  line-height:1.18!important;
  margin-top:.20rem!important;
  margin-bottom:.35rem!important;
}}

h2 {{
  font-size:{h2}!important;
  line-height:1.18!important;
  margin-top:.20rem!important;
  margin-bottom:.30rem!important;
}}

h3 {{
  font-size:{h3}!important;
  line-height:1.18!important;
  margin-top:.18rem!important;
  margin-bottom:.25rem!important;
}}

p, li, label, span, div, small {{
  font-size:{font}!important;
}}

.stMarkdown, .stMarkdown * {{
  font-size:{font}!important;
  line-height:1.35!important;
}}

.glass-card,
.metric-glass,
.inner-glass,
.telegram-card,
.ocean-card,
.card,
.profile-glass {{
  background: linear-gradient(135deg, rgba(255,255,255,.80), rgba(240,249,255,.66))!important;
  border:1px solid rgba(14,116,144,.14)!important;
  border-radius:{radius}!important;
  padding:{card_pad}!important;
  backdrop-filter: blur(18px) saturate(175%)!important;
  box-shadow:0 6px 18px rgba(2,132,199,.07), inset 0 1px 0 rgba(255,255,255,.72)!important;
  animation: fadeUp .25s ease both;
  overflow-wrap:anywhere!important;
}}

.stButton>button {{
  width:100%;
  min-height:{btn_h}!important;
  border-radius:{radius}!important;
  border:1px solid rgba(14,116,144,.15)!important;
  background: linear-gradient(135deg, rgba(255,255,255,.82), rgba(224,242,254,.60))!important;
  color:#0f172a!important;
  font-weight:800!important;
  font-size:{font}!important;
  padding:5px 8px!important;
  backdrop-filter: blur(16px)!important;
  box-shadow:0 4px 12px rgba(2,132,199,.07)!important;
}}

.stButton>button:hover {{
  background:rgba(224,242,254,.74)!important;
  transform: translateY(-1px);
}}

div[data-testid="metric-container"] {{
  background: rgba(255,255,255,.78)!important;
  border:1px solid rgba(14,116,144,.13)!important;
  border-radius:{radius}!important;
  padding:{card_pad}!important;
  backdrop-filter: blur(16px)!important;
  box-shadow:0 4px 12px rgba(2,132,199,.06)!important;
}}

div[data-testid="metric-container"] label {{
  color:#075985!important;
  font-size:{font}!important;
  font-weight:800!important;
}}

div[data-testid="metric-container"] [data-testid="stMetricValue"] {{
  color:#0f172a!important;
  font-size:{metric_v}!important;
  font-weight:900!important;
}}

.stTabs [data-baseweb="tab-list"] {{
  gap:4px!important;
  flex-wrap:wrap!important;
  background:rgba(255,255,255,.46)!important;
  border-radius:{radius}!important;
  padding:4px!important;
}}

.stTabs [data-baseweb="tab"] {{
  border-radius:{radius}!important;
  padding:5px 7px!important;
  background:rgba(255,255,255,.66)!important;
  color:#0f172a!important;
  font-size:{tab_font}!important;
  min-height:28px!important;
  font-weight:800!important;
}}

.stTabs [aria-selected="true"] {{
  background:rgba(186,230,253,.76)!important;
  color:#075985!important;
}}

input, textarea, select,
div[data-baseweb="input"] input,
div[data-baseweb="textarea"] textarea {{
  background:rgba(255,255,255,.84)!important;
  color:#0f172a!important;
  border-radius:{radius}!important;
  font-size:{font}!important;
  border:1px solid rgba(14,116,144,.16)!important;
}}

[data-testid="stDataFrame"],
[data-testid="stDataFrame"] * {{
  font-size:{font}!important;
}}

div[data-testid="column"] {{
  padding-left:0.16rem!important;
  padding-right:0.16rem!important;
}}

.badge-buy,
.badge-sell,
.badge-neutral,
.engine-timer-box,
.engine-warning,
.stat-box {{
  border-radius:{radius}!important;
  padding:{card_pad}!important;
  font-size:{font}!important;
}}

.engine-timer-title,
.stat-title {{
  font-size:{font}!important;
}}

.engine-timer-value,
.stat-value {{
  font-size:{metric_v}!important;
}}

::-webkit-scrollbar {{
  width:6px;
  height:6px;
}}

::-webkit-scrollbar-thumb {{
  background:rgba(14,116,144,.25);
  border-radius:999px;
}}

::-webkit-scrollbar-track {{
  background:rgba(255,255,255,.35);
}}

@keyframes fadeUp {{
  from {{ opacity:0; transform:translateY(5px); }}
  to {{ opacity:1; transform:translateY(0); }}
}}

@media(max-width:430px) {{
  .main .block-container {{
    max-width:360px!important;
    width:360px!important;
    min-width:360px!important;
    padding:0.42rem!important;
    margin-left:auto!important;
    margin-right:auto!important;
  }}

  html, body, [class*="css"],
  p, li, label, span, div, small,
  .stMarkdown, .stMarkdown * {{
    font-size:10px!important;
    line-height:1.35!important;
  }}

  h1 {{
    font-size:1rem!important;
    line-height:1.15!important;
  }}

  h2 {{
    font-size:.90rem!important;
    line-height:1.15!important;
  }}

  h3 {{
    font-size:.82rem!important;
    line-height:1.15!important;
  }}

  .stButton>button {{
    min-height:34px!important;
    font-size:10px!important;
    padding:5px 7px!important;
    border-radius:13px!important;
  }}

  div[data-testid="metric-container"] {{
    padding:8px!important;
    border-radius:13px!important;
  }}

  div[data-testid="metric-container"] label {{
    font-size:9.5px!important;
  }}

  div[data-testid="metric-container"] [data-testid="stMetricValue"] {{
    font-size:15.5px!important;
  }}

  .stTabs [data-baseweb="tab"] {{
    font-size:9px!important;
    padding:5px 6px!important;
    min-height:27px!important;
  }}

  .ocean-card,
  .glass-card,
  .inner-glass,
  .card,
  .profile-glass {{
    padding:8px!important;
    border-radius:13px!important;
  }}

  section[data-testid="stSidebar"] {{
    width:230px!important;
    min-width:230px!important;
  }}

  div[data-testid="column"] {{
    padding-left:0.12rem!important;
    padding-right:0.12rem!important;
  }}

  .row-widget.stSelectbox,
  .row-widget.stTextInput,
  .row-widget.stNumberInput {{
    width:100%!important;
  }}

  .block-container > div {{
    max-width:100%!important;
  }}
}}

@media(max-width:380px) {{
  .main .block-container {{
    max-width:340px!important;
    width:340px!important;
    min-width:340px!important;
    padding:0.36rem!important;
  }}

  html, body, [class*="css"],
  p, li, label, span, div, small,
  .stMarkdown, .stMarkdown * {{
    font-size:9.5px!important;
  }}

  .stButton>button {{
    min-height:32px!important;
    font-size:9.5px!important;
  }}
}}
</style>
""", unsafe_allow_html=True)


def auto_close_sidebar_script():
    st.markdown(r"""
<script>
function closeStreamlitSidebar(){
 const doc = window.parent.document;
 const buttons = [...doc.querySelectorAll('button')];
 const closeBtn = buttons.find(b =>
   (b.getAttribute('aria-label') || '').toLowerCase().includes('close sidebar')
 );
 if(closeBtn){
   setTimeout(() => closeBtn.click(), 80);
 }
}
window.addEventListener('message', (e) => {
 if(e.data === 'close-sidebar') closeStreamlitSidebar();
});
</script>
""", unsafe_allow_html=True)


def request_close_sidebar():
    st.markdown(
        "<script>window.parent.postMessage('close-sidebar','*');</script>",
        unsafe_allow_html=True
    )


def load_style(phone_mode: bool = False):
    apply_global_styles(phone_mode=phone_mode)


def apply_style(phone_mode: bool = False):
    apply_global_styles(phone_mode=phone_mode)
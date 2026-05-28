import streamlit as st


def apply_global_styles(phone_mode: bool = False):
    maxw = "390px" if phone_mode else "1180px"
    pad = "0.18rem 0.22rem" if phone_mode else "0.85rem 1.20rem"
    font = "7.5px" if phone_mode else "11px"
    h1 = "0.72rem" if phone_mode else "1.25rem"
    h2 = "0.66rem" if phone_mode else "1.05rem"
    h3 = "0.62rem" if phone_mode else "0.92rem"
    btn_h = "20px" if phone_mode else "36px"
    metric_v = "10px" if phone_mode else "18px"
    tab_font = "6.8px" if phone_mode else "10.5px"
    card_pad = "4px" if phone_mode else "10px"
    radius = "9px" if phone_mode else "18px"

    st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

:root {{
  --glass: rgba(255,255,255,.76);
  --glass2: rgba(240,249,255,.58);
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
    radial-gradient(circle at top left, rgba(224,242,254,.70), transparent 30%),
    radial-gradient(circle at top right, rgba(219,234,254,.58), transparent 34%),
    radial-gradient(circle at bottom right, rgba(240,249,255,.80), transparent 38%),
    linear-gradient(135deg,#f8fbff 0%,#eef8ff 45%,#f8fafc 100%) !important;
  background-attachment: fixed;
}}

.main .block-container {{
  max-width:{maxw}!important;
  padding:{pad}!important;
  margin-left:auto!important;
  margin-right:auto!important;
}}

section[data-testid="stSidebar"] {{
  background: rgba(248,252,255,.74)!important;
  backdrop-filter: blur(26px) saturate(170%)!important;
  border-right:1px solid rgba(14,116,144,.14)!important;
}}

section[data-testid="stSidebar"] * {{
  font-size:{font}!important;
}}

h1 {{
  font-size:{h1}!important;
  line-height:1.15!important;
  margin-top:.15rem!important;
  margin-bottom:.25rem!important;
}}

h2 {{
  font-size:{h2}!important;
  line-height:1.15!important;
  margin-top:.15rem!important;
  margin-bottom:.20rem!important;
}}

h3 {{
  font-size:{h3}!important;
  line-height:1.15!important;
  margin-top:.12rem!important;
  margin-bottom:.18rem!important;
}}

p, li, label, span, div, small {{
  font-size:{font}!important;
}}

.stMarkdown, .stMarkdown * {{
  font-size:{font}!important;
  line-height:1.25!important;
}}

.glass-card,
.metric-glass,
.inner-glass,
.telegram-card,
.ocean-card,
.card,
.profile-glass {{
  background: linear-gradient(135deg, rgba(255,255,255,.78), rgba(240,249,255,.60))!important;
  border:1px solid rgba(14,116,144,.14)!important;
  border-radius:{radius}!important;
  padding:{card_pad}!important;
  backdrop-filter: blur(18px) saturate(175%)!important;
  box-shadow:0 6px 18px rgba(2,132,199,.07), inset 0 1px 0 rgba(255,255,255,.70)!important;
  animation: fadeUp .25s ease both;
}}

.glass-card:hover,
.metric-glass:hover,
.inner-glass:hover,
.telegram-card:hover,
.ocean-card:hover,
.card:hover,
.profile-glass:hover {{
  transform: translateY(-1px);
  box-shadow:0 8px 22px rgba(2,132,199,.10)!important;
}}

.stButton>button {{
  width:100%;
  min-height:{btn_h}!important;
  border-radius:{radius}!important;
  border:1px solid rgba(14,116,144,.15)!important;
  background: linear-gradient(135deg, rgba(255,255,255,.80), rgba(224,242,254,.55))!important;
  color:#0f172a!important;
  font-weight:800!important;
  font-size:{font}!important;
  padding:1px 4px!important;
  backdrop-filter: blur(16px)!important;
  box-shadow:0 4px 12px rgba(2,132,199,.07)!important;
}}

.stButton>button:hover {{
  background:rgba(224,242,254,.70)!important;
  transform: translateY(-1px);
}}

div[data-testid="metric-container"] {{
  background: rgba(255,255,255,.76)!important;
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
  gap:3px!important;
  flex-wrap:wrap!important;
  background:rgba(255,255,255,.42)!important;
  border-radius:{radius}!important;
  padding:3px!important;
}}

.stTabs [data-baseweb="tab"] {{
  border-radius:{radius}!important;
  padding:3px 5px!important;
  background:rgba(255,255,255,.62)!important;
  color:#0f172a!important;
  font-size:{tab_font}!important;
  min-height:18px!important;
  font-weight:800!important;
}}

.stTabs [aria-selected="true"] {{
  background:rgba(186,230,253,.72)!important;
  color:#075985!important;
}}

input, textarea, select,
div[data-baseweb="input"] input,
div[data-baseweb="textarea"] textarea {{
  background:rgba(255,255,255,.82)!important;
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
  padding-left:0.08rem!important;
  padding-right:0.08rem!important;
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
  width:5px;
  height:5px;
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
    max-width:390px!important;
    width:390px!important;
    padding:0.12rem 0.18rem!important;
    margin-left:auto!important;
    margin-right:auto!important;
  }}

  html, body, [class*="css"],
  p, li, label, span, div, small,
  .stMarkdown, .stMarkdown * {{
    font-size:7px!important;
    line-height:1.20!important;
  }}

  h1 {{
    font-size:.68rem!important;
  }}

  h2 {{
    font-size:.62rem!important;
  }}

  h3 {{
    font-size:.58rem!important;
  }}

  .stButton>button {{
    min-height:19px!important;
    font-size:6.8px!important;
    padding:0 3px!important;
    border-radius:8px!important;
  }}

  div[data-testid="metric-container"] {{
    padding:3px!important;
    border-radius:8px!important;
  }}

  div[data-testid="metric-container"] label {{
    font-size:6.5px!important;
  }}

  div[data-testid="metric-container"] [data-testid="stMetricValue"] {{
    font-size:9.5px!important;
  }}

  .stTabs [data-baseweb="tab"] {{
    font-size:6.3px!important;
    padding:2px 3px!important;
    min-height:16px!important;
  }}

  .ocean-card,
  .glass-card,
  .inner-glass,
  .card,
  .profile-glass {{
    padding:3px!important;
    border-radius:8px!important;
  }}

  section[data-testid="stSidebar"] {{
    width:210px!important;
    min-width:210px!important;
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
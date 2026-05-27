import streamlit as st
import requests
import math

# ─────────────────────────────────────────────
#  CONFIG
# ─────────────────────────────────────────────
API_URL = "http://127.0.0.1:8000/predict"

TIER_1 = {"Mumbai", "Delhi", "Bangalore", "Chennai", "Kolkata", "Hyderabad", "Pune"}
TIER_2 = {
    "Jaipur", "Chandigarh", "Indore", "Lucknow", "Patna", "Ranchi", "Visakhapatnam",
    "Coimbatore", "Bhopal", "Nagpur", "Vadodara", "Surat", "Rajkot", "Jodhpur", "Raipur",
    "Amritsar", "Varanasi", "Agra", "Dehradun", "Mysore", "Jabalpur", "Guwahati",
    "Thiruvananthapuram", "Ludhiana", "Nashik", "Allahabad", "Udaipur", "Aurangabad", "Noida",
}

OCCUPATIONS = [
    "private_job", "government_job", "business_owner",
    "freelancer", "student", "retired", "unemployed",
]

# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────
def get_bmi(weight, height):
    if height <= 0:
        return 0.0
    return round(weight / (height ** 2), 1)

def bmi_category(bmi):
    if bmi < 18.5:  return "Underweight", "#38bdf8"
    if bmi < 25.0:  return "Normal",      "#34d399"
    if bmi < 30.0:  return "Overweight",  "#fb923c"
    return "Obese", "#f87171"

def get_lifestyle_risk(smoker, bmi):
    if smoker and bmi > 30:  return "high"
    if smoker or bmi > 27:   return "medium"
    return "low"

def get_age_group(age):
    if age < 25:   return "young"
    if age < 45:   return "adult"
    if age < 60:   return "middle_aged"
    return "senior"

def get_city_tier(city):
    if city in TIER_1: return 1
    if city in TIER_2: return 2
    return 3

RISK_PALETTE = {
    "low":    {"glow": "#10b981", "grad": "linear-gradient(135deg,#052e16 0%,#064e3b 100%)",
               "accent": "#34d399", "badge_bg": "#064e3b", "badge_fg": "#6ee7b7", "label": "LOW RISK",
               "rgb": "16,185,129"},
    "medium": {"glow": "#f59e0b", "grad": "linear-gradient(135deg,#1c1003 0%,#3b2000 100%)",
               "accent": "#fbbf24", "badge_bg": "#3b2000", "badge_fg": "#fcd34d", "label": "MEDIUM RISK",
               "rgb": "245,158,11"},
    "high":   {"glow": "#ef4444", "grad": "linear-gradient(135deg,#1a0000 0%,#3b0000 100%)",
               "accent": "#f87171", "badge_bg": "#3b0000", "badge_fg": "#fca5a5", "label": "HIGH RISK",
               "rgb": "239,68,68"},
}

def arc_svg(value, max_val, color, size=160):
    cx, cy, r = size // 2, size // 2, (size // 2) - 18
    circ = math.pi * r
    pct = min(value / max_val, 1.0)
    dash = pct * circ
    return f"""
    <svg width="{size}" height="{size//2 + 14}" viewBox="0 0 {size} {size//2+14}" xmlns="http://www.w3.org/2000/svg">
      <path d="M 18 {cy} A {r} {r} 0 0 1 {size-18} {cy}"
            fill="none" stroke="#1e293b" stroke-width="10" stroke-linecap="round"/>
      <path d="M 18 {cy} A {r} {r} 0 0 1 {size-18} {cy}"
            fill="none" stroke="{color}" stroke-width="10" stroke-linecap="round"
            stroke-dasharray="{dash:.1f} {circ:.1f}"/>
      <text x="{cx}" y="{cy + 2}" text-anchor="middle"
            font-size="22" font-weight="700" fill="{color}" font-family="'DM Sans', sans-serif">{value}</text>
      <text x="{cx}" y="{cy + 16}" text-anchor="middle"
            font-size="10" fill="#64748b" font-family="'DM Sans', sans-serif">BMI</text>
    </svg>"""

def prob_bar_html(label, prob, color, is_winner=False):
    pct = round(prob * 100, 1)
    border = f"1px solid {color}50" if is_winner else "1px solid #1e293b"
    bg     = f"{color}12"           if is_winner else "#060e1e"
    glow   = f"0 0 20px {color}30" if is_winner else "none"
    return f"""
    <div style="margin-bottom:12px; padding:16px 18px; border-radius:14px;
                background:{bg}; border:{border}; box-shadow:{glow}; transition:all 0.3s;">
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
        <div style="display:flex; align-items:center; gap:8px;">
          {"<div style='width:7px;height:7px;border-radius:50%;background:" + color + ";box-shadow:0 0 6px " + color + ";'></div>" if is_winner else "<div style='width:7px;height:7px;border-radius:50%;background:#1e293b;'></div>"}
          <span style="font-size:12px; font-weight:600; color:{'#e2e8f0' if is_winner else '#64748b'};
                       letter-spacing:0.06em; text-transform:uppercase; font-family:'DM Sans',sans-serif;">{label}</span>
        </div>
        <span style="font-size:18px; font-weight:700; color:{color}; font-family:'DM Sans',sans-serif;">{pct}%</span>
      </div>
      <div style="height:5px; background:#0f172a; border-radius:100px; overflow:hidden;">
        <div style="height:100%; width:{pct}%; background:linear-gradient(90deg, {color}80, {color});
                    border-radius:100px;"></div>
      </div>
    </div>"""

# ─────────────────────────────────────────────
#  PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="PremiumIQ — Insurance Estimator",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────
#  GLOBAL CSS
# ─────────────────────────────────────────────
st.markdown("""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700;0,9..40,800;1,9..40,300&family=DM+Mono:wght@400;500&display=swap" rel="stylesheet">

<style>
*, *::before, *::after { box-sizing: border-box; }

html, body, [data-testid="stAppViewContainer"],
[data-testid="stMain"], .main { background: #020817 !important; }

[data-testid="stAppViewContainer"] {
    background:
        radial-gradient(ellipse 70% 45% at 15% -5%, #0d2d5e 0%, transparent 55%),
        radial-gradient(ellipse 55% 40% at 85% 105%, #1a053a 0%, transparent 50%),
        radial-gradient(ellipse 40% 30% at 50% 50%, #05111f 0%, transparent 70%),
        #020817 !important;
    min-height: 100vh;
}

[data-testid="stHeader"] { background: transparent !important; }
[data-testid="stSidebar"] { background: #040d1e !important; }

section.main .block-container {
    max-width: 1200px;
    padding: 3rem 2.5rem 6rem;
    margin: 0 auto;
}

html, body, [class*="css"], .stMarkdown, p, span, label,
.stSelectbox, .stNumberInput, .stTextInput {
    font-family: 'DM Sans', sans-serif !important;
    color: #cbd5e1;
}

input[type="number"], input[type="text"] {
    background: #0b1527 !important;
    border: 1px solid #1e2d45 !important;
    border-radius: 10px !important;
    color: #e2e8f0 !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 15px !important;
    padding: 0.55rem 1rem !important;
    transition: border-color 0.25s, box-shadow 0.25s !important;
}
input[type="number"]:focus, input[type="text"]:focus {
    border-color: #4f46e5 !important;
    box-shadow: 0 0 0 3px #4f46e518 !important;
    outline: none !important;
}

[data-baseweb="select"] > div,
[data-baseweb="select"] > div:hover {
    background: #0b1527 !important;
    border: 1px solid #1e2d45 !important;
    border-radius: 10px !important;
    color: #e2e8f0 !important;
    font-family: 'DM Sans', sans-serif !important;
}
[data-baseweb="select"] svg { fill: #475569 !important; }
[data-baseweb="popover"] { background: #0b1527 !important; border: 1px solid #1e2d45 !important; border-radius: 12px !important; }
[role="option"] { background: #0b1527 !important; color: #cbd5e1 !important; }
[role="option"]:hover { background: #1e293b !important; }

label[data-testid="stWidgetLabel"] p,
.stNumberInput label, .stTextInput label, .stSelectbox label {
    font-size: 11px !important;
    font-weight: 600 !important;
    letter-spacing: 0.09em !important;
    text-transform: uppercase !important;
    color: #3d5a80 !important;
    margin-bottom: 5px !important;
}

.stButton > button {
    width: 100% !important;
    background: linear-gradient(135deg, #4338ca 0%, #6d28d9 100%) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 0.95rem 2rem !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 15px !important;
    font-weight: 700 !important;
    letter-spacing: 0.05em !important;
    text-transform: uppercase !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 4px 30px #4338ca35 !important;
    cursor: pointer !important;
}
.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 40px #6d28d950 !important;
    background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%) !important;
}
.stButton > button:active { transform: translateY(0) !important; }

[data-testid="stSpinner"] { color: #4f46e5 !important; }
#MainMenu, footer, header { visibility: hidden; }
[data-testid="stDecoration"] { display: none; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  HERO HEADER
# ─────────────────────────────────────────────
st.markdown("""
<div style="text-align:center; padding: 3rem 0 2.8rem;">
    <div style="display:inline-flex; align-items:center; gap:7px; background:#0b1527;
                border:1px solid #1e2d45; border-radius:100px; padding:5px 16px; margin-bottom:1.4rem;">
        <div style="width:6px;height:6px;border-radius:50%;background:#4f46e5;box-shadow:0 0 8px #4f46e5;"></div>
        <span style="font-size:11px; font-weight:600; letter-spacing:0.14em;
                     text-transform:uppercase; color:#4f46e5; font-family:'DM Sans',sans-serif;">
            ML-Powered · v1.0
        </span>
    </div>
    <h1 style="font-family:'DM Sans',sans-serif; font-size:clamp(2.4rem,5vw,4rem);
               font-weight:800; color:#f1f5f9; letter-spacing:-0.04em;
               line-height:1.08; margin:0 0 1.1rem;">
        Insurance Premium
        <span style="background:linear-gradient(100deg,#6366f1 0%,#a78bfa 50%,#38bdf8 100%);
                     -webkit-background-clip:text; -webkit-text-fill-color:transparent;
                     background-clip:text;"> Intelligence</span>
    </h1>
    <p style="font-family:'DM Sans',sans-serif; font-size:1rem; color:#475569;
              max-width:480px; margin:0 auto; font-weight:300; line-height:1.75;">
        Enter your profile below. Our ML model analyses 7 risk factors
        and returns your premium tier with full probability breakdown.
    </p>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  FORM
# ─────────────────────────────────────────────
LEFT, RIGHT = st.columns([1.05, 0.95], gap="large")

with LEFT:
    st.markdown("""
    <div style="background:linear-gradient(145deg,#0a1628,#0d1f3c); border:1px solid #1a2d4a;
                border-radius:20px; padding:1.8rem 1.8rem 1.4rem; margin-bottom:1.2rem;">
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:1.4rem;">
            <div style="width:3px;height:18px;border-radius:2px;background:linear-gradient(180deg,#4f46e5,#7c3aed);"></div>
            <span style="font-family:'DM Sans',sans-serif; font-size:11px; font-weight:700;
                      letter-spacing:0.15em; text-transform:uppercase; color:#4f46e5;">
                Biometric Data
            </span>
        </div>
    """, unsafe_allow_html=True)

    b1, b2 = st.columns(2)
    with b1:
        age    = st.number_input("Age (years)", min_value=1, max_value=119, value=30)
        weight = st.number_input("Weight (kg)",  min_value=1.0, step=0.5, value=70.0)
    with b2:
        height = st.number_input("Height (m)",  min_value=0.5, max_value=2.5, step=0.01, value=1.70)
        city   = st.text_input("City", value="Mumbai", placeholder="Mumbai, Jaipur…")

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("""
    <div style="background:linear-gradient(145deg,#0a1628,#0d1f3c); border:1px solid #1a2d4a;
                border-radius:20px; padding:1.8rem 1.8rem 1.4rem; margin-bottom:1.2rem;">
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:1.4rem;">
            <div style="width:3px;height:18px;border-radius:2px;background:linear-gradient(180deg,#4f46e5,#7c3aed);"></div>
            <span style="font-family:'DM Sans',sans-serif; font-size:11px; font-weight:700;
                      letter-spacing:0.15em; text-transform:uppercase; color:#4f46e5;">
                Financial Profile
            </span>
        </div>
    """, unsafe_allow_html=True)

    f1, f2 = st.columns(2)
    with f1:
        income_lpa = st.number_input("Annual income (LPA)", min_value=0.1, step=0.5, value=10.0)
    with f2:
        occupation = st.selectbox("Occupation", OCCUPATIONS,
                                  format_func=lambda x: x.replace("_", " ").title())

    smoker = st.selectbox("Smoking status",
                          options=[False, True],
                          format_func=lambda x: "🚬  Smoker" if x else "🚭  Non-smoker")

    st.markdown("</div>", unsafe_allow_html=True)

    predict_clicked = st.button("⚡  Analyse My Premium", type="primary")

with RIGHT:
    bmi_live   = get_bmi(weight, height)
    risk_live  = get_lifestyle_risk(smoker, bmi_live)
    ag_live    = get_age_group(age)
    tier_live  = get_city_tier(city)
    bmi_cat, bmi_col = bmi_category(bmi_live)
    risk_pal   = RISK_PALETTE[risk_live]
    gauge_svg  = arc_svg(bmi_live, 45, bmi_col, size=170)

    # ── Live preview shell
    st.markdown(f"""
    <div style="background:linear-gradient(145deg,#0a1628,#0d1f3c); border:1px solid #1a2d4a;
                border-radius:20px; padding:1.8rem; margin-bottom:1.2rem; position:relative; overflow:hidden;">
      <div style="position:absolute;top:-40px;right:-40px;width:160px;height:160px;
                  background:radial-gradient(circle,{risk_pal['glow']}18 0%,transparent 70%);
                  border-radius:50%; pointer-events:none;"></div>

      <div style="display:flex;align-items:center;gap:8px;margin-bottom:1.4rem;">
        <div style="width:3px;height:18px;border-radius:2px;background:linear-gradient(180deg,#4f46e5,#7c3aed);"></div>
        <span style="font-family:'DM Sans',sans-serif; font-size:11px; font-weight:700;
                  letter-spacing:0.15em; text-transform:uppercase; color:#4f46e5;">
            Live Profile Preview
        </span>
      </div>

      <div style="display:flex; align-items:center; margin-bottom:1.4rem; gap:1rem;">
        <div>{gauge_svg}</div>
        <div>
          <div style="font-size:10px; color:#3d5a80; text-transform:uppercase;
                      letter-spacing:0.1em; margin-bottom:4px; font-family:'DM Sans',sans-serif;">BMI Status</div>
          <div style="font-family:'DM Sans',sans-serif; font-size:24px; font-weight:800;
                      color:{bmi_col}; letter-spacing:-0.02em;">{bmi_cat}</div>
          <div style="font-family:'DM Mono',monospace; font-size:12px; color:#475569; margin-top:3px;">{bmi_live} kg/m²</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Stats grid — FIXED: each card is its own st.markdown call
    g1, g2 = st.columns(2)
    with g1:
        st.markdown(f"""
        <div style="background:#060e1e; border:1px solid #1a2d4a; border-radius:14px;
                    padding:14px 16px; margin-bottom:10px;">
          <div style="font-size:10px; color:#3d5a80; text-transform:uppercase;
                      letter-spacing:0.1em; margin-bottom:7px; font-family:'DM Sans',sans-serif;">Lifestyle Risk</div>
          <div style="display:flex; align-items:center; gap:7px;">
            <div style="width:8px; height:8px; border-radius:50%; background:{risk_pal['glow']};
                        box-shadow:0 0 8px {risk_pal['glow']};"></div>
            <span style="font-family:'DM Sans',sans-serif; font-size:15px; font-weight:700;
                         color:{risk_pal['glow']};">{risk_live.upper()}</span>
          </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div style="background:#060e1e; border:1px solid #1a2d4a; border-radius:14px;
                    padding:14px 16px; margin-bottom:10px;">
          <div style="font-size:10px; color:#3d5a80; text-transform:uppercase;
                      letter-spacing:0.1em; margin-bottom:7px; font-family:'DM Sans',sans-serif;">City Tier</div>
          <div style="font-family:'DM Sans',sans-serif; font-size:15px; font-weight:700;
                      color:#38bdf8;">Tier {tier_live} — {city if city else "—"}</div>
        </div>
        """, unsafe_allow_html=True)

    with g2:
        st.markdown(f"""
        <div style="background:#060e1e; border:1px solid #1a2d4a; border-radius:14px;
                    padding:14px 16px; margin-bottom:10px;">
          <div style="font-size:10px; color:#3d5a80; text-transform:uppercase;
                      letter-spacing:0.1em; margin-bottom:7px; font-family:'DM Sans',sans-serif;">Age Group</div>
          <div style="font-family:'DM Sans',sans-serif; font-size:15px; font-weight:700;
                      color:#a78bfa;">{ag_live.replace('_', ' ').title()}</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div style="background:#060e1e; border:1px solid #1a2d4a; border-radius:14px;
                    padding:14px 16px; margin-bottom:10px;">
          <div style="font-size:10px; color:#3d5a80; text-transform:uppercase;
                      letter-spacing:0.1em; margin-bottom:7px; font-family:'DM Sans',sans-serif;">Income</div>
          <div style="font-family:'DM Mono',monospace; font-size:15px; font-weight:500;
                      color:#e2e8f0;">₹{income_lpa} LPA</div>
        </div>
        """, unsafe_allow_html=True)

    # ── How it works
    st.markdown("""
    <div style="background:linear-gradient(145deg,#0a1628,#0d1f3c); border:1px solid #1a2d4a;
                border-radius:18px; padding:1.3rem 1.5rem; margin-top:0.2rem;">
      <div style="font-size:10px; color:#3d5a80; text-transform:uppercase;
                  letter-spacing:0.12em; margin-bottom:12px; font-family:'DM Sans',sans-serif;">How it works</div>
    """, unsafe_allow_html=True)

    for i, t in [
        ("1", "Your inputs are converted to derived risk features"),
        ("2", "A trained ML pipeline classifies your profile"),
        ("3", "You receive your category + full probability breakdown"),
    ]:
        st.markdown(f"""
        <div style="display:flex; align-items:flex-start; gap:10px; margin-bottom:9px;">
          <div style="min-width:20px; height:20px; background:#0f172a; border:1px solid #1e2d45;
                      border-radius:6px; display:flex; align-items:center; justify-content:center;
                      font-size:10px; font-weight:700; color:#4f46e5; font-family:'DM Mono',monospace;
                      margin-top:1px;">{i}</div>
          <span style="font-size:12px; color:#475569; line-height:1.6; font-family:'DM Sans',sans-serif;">{t}</span>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  PREDICTION RESULT
# ─────────────────────────────────────────────
if predict_clicked:
    bmi            = get_bmi(weight, height)
    lifestyle_risk = get_lifestyle_risk(smoker, bmi)
    age_group      = get_age_group(age)
    city_tier      = get_city_tier(city)

    payload = {
        "age": age,
        "weight": weight,
        "height": height,
        "income_lpa": income_lpa,
        "smoker": smoker,
        "city": city,
        "occupation": occupation
    }

    try:
        with st.spinner("Running inference…"):
            resp   = requests.post(API_URL, json=payload, timeout=10)
            result = resp.json()

        if resp.status_code != 200:
            st.error(f"API error {resp.status_code}: {result}")
            st.stop()

        category     = str(result.get("predicted_category", "unknown")).lower()
        confidence   = float(result.get("confidence", 0.0))
        class_probs  = result.get("class_probabilities", {})
        pal          = RISK_PALETTE.get(category, RISK_PALETTE["medium"])
        conf_pct     = round(confidence * 100, 1)

        # ── Divider
        st.markdown("""
        <div style="display:flex;align-items:center;gap:16px;margin:2.5rem 0 1.8rem;">
          <div style="flex:1;height:1px;background:linear-gradient(90deg,transparent,#1e2d45);"></div>
          <span style="font-size:10px;font-weight:700;letter-spacing:0.15em;text-transform:uppercase;
                       color:#4f46e5;font-family:'DM Sans',sans-serif;">Prediction Result</span>
          <div style="flex:1;height:1px;background:linear-gradient(90deg,#1e2d45,transparent);"></div>
        </div>
        """, unsafe_allow_html=True)

        # ── Hero result banner
        st.markdown(f"""
        <div style="background:{pal['grad']}; border:1px solid {pal['glow']}35;
                    border-radius:24px; padding:2.5rem 3rem; position:relative;
                    overflow:hidden; margin-bottom:1.5rem;">

          <div style="position:absolute;top:-80px;right:-80px;width:300px;height:300px;
                      background:radial-gradient(circle,{pal['glow']}18 0%,transparent 65%);
                      border-radius:50%; pointer-events:none;"></div>
          <div style="position:absolute;bottom:-50px;left:-50px;width:220px;height:220px;
                      background:radial-gradient(circle,{pal['glow']}10 0%,transparent 65%);
                      border-radius:50%; pointer-events:none;"></div>

          <div style="display:flex; align-items:center; gap:10px; margin-bottom:1.2rem; flex-wrap:wrap;">
            <div style="background:{pal['badge_bg']}; border:1px solid {pal['glow']}45;
                        border-radius:100px; padding:5px 14px; display:inline-flex; align-items:center; gap:6px;">
              <div style="width:6px;height:6px;border-radius:50%;background:{pal['glow']};
                          box-shadow:0 0 6px {pal['glow']};"></div>
              <span style="font-size:10px; font-weight:700; letter-spacing:0.14em;
                           text-transform:uppercase; color:{pal['badge_fg']};
                           font-family:'DM Sans',sans-serif;">{pal['label']}</span>
            </div>
            <div style="background:{pal['badge_bg']}; border:1px solid {pal['glow']}45;
                        border-radius:100px; padding:5px 14px;">
              <span style="font-size:10px; font-weight:700; letter-spacing:0.1em;
                           color:{pal['badge_fg']}; font-family:'DM Mono',monospace;">
                CONFIDENCE · {conf_pct}%
              </span>
            </div>
          </div>

          <div style="font-family:'DM Sans',sans-serif; font-size:clamp(2rem,4vw,3.2rem);
                      font-weight:800; color:#f1f5f9; letter-spacing:-0.04em; margin-bottom:0.5rem;">
            {category.title()} Premium
            <span style="color:{pal['glow']};">Category</span>
          </div>
          <p style="font-size:14px; color:#64748b; margin:0 0 2rem; max-width:520px;
                    line-height:1.7; font-family:'DM Sans',sans-serif;">
            Based on your biometric, lifestyle and financial profile, our model
            predicts your health insurance falls into the
            <strong style="color:{pal['accent']};">{category} premium</strong> bracket.
          </p>

          <div>
            <div style="display:flex;justify-content:space-between;align-items:center;
                        margin-bottom:6px;">
              <div style="font-size:10px; color:#475569; text-transform:uppercase;
                          letter-spacing:0.1em; font-family:'DM Sans',sans-serif;">Model Confidence</div>
              <div style="font-family:'DM Mono',monospace; font-size:11px; color:{pal['glow']};">{conf_pct}%</div>
            </div>
            <div style="height:6px; background:#ffffff10; border-radius:100px;
                        overflow:hidden; max-width:500px;">
              <div style="height:100%; width:{conf_pct}%;
                          background:linear-gradient(90deg,{pal['glow']}70,{pal['glow']});
                          border-radius:100px;"></div>
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        # ── Breakdown row
        col_prob, col_stats = st.columns([1.1, 0.9], gap="large")

        with col_prob:
            st.markdown(f"""
            <div style="background:linear-gradient(145deg,#0a1628,#0d1f3c); border:1px solid #1a2d4a;
                        border-radius:20px; padding:1.8rem;">
              <div style="display:flex;align-items:center;gap:8px;margin-bottom:1.4rem;">
                <div style="width:3px;height:18px;border-radius:2px;background:linear-gradient(180deg,#4f46e5,#7c3aed);"></div>
                <span style="font-family:'DM Sans',sans-serif; font-size:11px; font-weight:700;
                          letter-spacing:0.15em; text-transform:uppercase; color:#4f46e5;">
                    Probability Breakdown
                </span>
              </div>
            """, unsafe_allow_html=True)

            BAR_COLORS = {"low": "#10b981", "medium": "#f59e0b", "high": "#ef4444"}
            sorted_probs = sorted(class_probs.items(), key=lambda x: x[1], reverse=True)
            for cls, prob in sorted_probs:
                is_winner = cls.lower() == category
                c = BAR_COLORS.get(cls.lower(), pal["glow"])
                st.markdown(prob_bar_html(cls.replace("_", " ").title(), prob, c, is_winner),
                            unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)

        with col_stats:
            bmi_cat_label, bmi_col2 = bmi_category(bmi)

            st.markdown(f"""
            <div style="background:linear-gradient(145deg,#0a1628,#0d1f3c); border:1px solid #1a2d4a;
                        border-radius:20px; padding:1.8rem;">
              <div style="display:flex;align-items:center;gap:8px;margin-bottom:1.4rem;">
                <div style="width:3px;height:18px;border-radius:2px;background:linear-gradient(180deg,#4f46e5,#7c3aed);"></div>
                <span style="font-family:'DM Sans',sans-serif; font-size:11px; font-weight:700;
                          letter-spacing:0.15em; text-transform:uppercase; color:#4f46e5;">
                    Risk Summary
                </span>
              </div>
            """, unsafe_allow_html=True)

            # FIXED: each row is its own st.markdown — no .join() nesting
            risk_rows = [
                ("BMI",            f"{bmi} — {bmi_cat_label}",           bmi_col2),
                ("Age group",      age_group.replace("_", " ").title(),   "#a78bfa"),
                ("Lifestyle risk", lifestyle_risk.upper(),                 pal["glow"]),
                ("City tier",      f"Tier {city_tier} · {city}",          "#38bdf8"),
                ("Income",         f"₹{income_lpa} LPA",                  "#e2e8f0"),
                ("Occupation",     occupation.replace("_", " ").title(),   "#94a3b8"),
                ("Smoker",         "Yes" if smoker else "No",
                                   "#f87171" if smoker else "#34d399"),
            ]
            for k, v, c in risk_rows:
                st.markdown(f"""
                <div style="display:flex; align-items:center; justify-content:space-between;
                            padding:11px 0; border-bottom:1px solid #0f172a;">
                  <span style="font-size:11px; color:#3d5a80; text-transform:uppercase;
                               letter-spacing:0.08em; font-family:'DM Sans',sans-serif;">{k}</span>
                  <span style="font-family:'DM Sans',sans-serif; font-size:13px;
                               font-weight:700; color:{c};">{v}</span>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)

        # ── Footer
        st.markdown("""
        <div style="margin-top:2rem; text-align:center; padding-bottom:1rem;">
          <span style="font-size:11px; color:#1e2d45; font-family:'DM Mono',monospace;">
            Prediction generated by ML model v1.0.0 &nbsp;·&nbsp; Not financial or medical advice
          </span>
        </div>
        """, unsafe_allow_html=True)

    except requests.exceptions.ConnectionError:
        st.error("❌  Cannot reach the FastAPI server on port 8000. Start it with `uvicorn main:app --reload`.")
    except requests.exceptions.Timeout:
        st.error("⏱️  Request timed out after 10 s. Check server health at `/health`.")
    except Exception as e:
        st.error(f"Unexpected error: {e}")
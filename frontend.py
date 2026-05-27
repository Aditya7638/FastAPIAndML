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
               "accent": "#34d399", "badge_bg": "#064e3b", "badge_fg": "#6ee7b7", "label": "LOW RISK"},
    "medium": {"glow": "#f59e0b", "grad": "linear-gradient(135deg,#1c1003 0%,#3b2000 100%)",
               "accent": "#fbbf24", "badge_bg": "#3b2000", "badge_fg": "#fcd34d", "label": "MEDIUM RISK"},
    "high":   {"glow": "#ef4444", "grad": "linear-gradient(135deg,#1a0000 0%,#3b0000 100%)",
               "accent": "#f87171", "badge_bg": "#3b0000", "badge_fg": "#fca5a5", "label": "HIGH RISK"},
}
 
def arc_svg(value, max_val, color, size=160):
    """Semicircular gauge SVG."""
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
            stroke-dasharray="{dash:.1f} {circ:.1f}"
            style="transition: stroke-dasharray 0.8s ease;"/>
      <text x="{cx}" y="{cy + 2}" text-anchor="middle"
            font-size="22" font-weight="700" fill="{color}" font-family="'Syne', sans-serif">{value}</text>
      <text x="{cx}" y="{cy + 16}" text-anchor="middle"
            font-size="10" fill="#64748b" font-family="'Syne', sans-serif">BMI</text>
    </svg>"""
 
def prob_bar_html(label, prob, color, is_winner=False):
    pct = round(prob * 100, 1)
    border = f"1px solid {color}40" if is_winner else "1px solid #1e293b"
    bg     = f"{color}18"           if is_winner else "#0f172a"
    return f"""
    <div style="margin-bottom:14px; padding:14px 16px; border-radius:12px;
                background:{bg}; border:{border}; transition:all 0.3s;">
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
        <span style="font-size:13px; font-weight:600; color:{'#e2e8f0' if is_winner else '#94a3b8'};
                     letter-spacing:0.04em; text-transform:uppercase;">{label}</span>
        <span style="font-size:16px; font-weight:700; color:{color};">{pct}%</span>
      </div>
      <div style="height:6px; background:#1e293b; border-radius:100px; overflow:hidden;">
        <div style="height:100%; width:{pct}%; background:linear-gradient(90deg, {color}aa, {color});
                    border-radius:100px; transition:width 1s ease;"></div>
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
<link href="https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=Epilogue:wght@300;400;500&display=swap" rel="stylesheet">
 
<style>
/* ── Reset & base ─────────────────────────────── */
*, *::before, *::after { box-sizing: border-box; }
 
html, body, [data-testid="stAppViewContainer"],
[data-testid="stMain"], .main { background: #020817 !important; }
 
[data-testid="stAppViewContainer"] {
    background:
        radial-gradient(ellipse 80% 50% at 20% -10%, #0f3460 0%, transparent 60%),
        radial-gradient(ellipse 60% 40% at 80% 110%, #1a0533 0%, transparent 55%),
        #020817 !important;
    min-height: 100vh;
}
 
[data-testid="stHeader"] { background: transparent !important; }
[data-testid="stSidebar"] { background: #040d1e !important; }
 
section.main .block-container {
    max-width: 1180px;
    padding: 3rem 2.5rem 5rem;
    margin: 0 auto;
}
 
/* ── Typography ───────────────────────────────── */
html, body, [class*="css"], .stMarkdown, p, span, label,
.stSelectbox, .stNumberInput, .stTextInput {
    font-family: 'Epilogue', sans-serif !important;
    color: #cbd5e1;
}
 
/* ── Inputs ───────────────────────────────────── */
input[type="number"], input[type="text"] {
    background: #0f172a !important;
    border: 1px solid #1e293b !important;
    border-radius: 12px !important;
    color: #e2e8f0 !important;
    font-family: 'Epilogue', sans-serif !important;
    font-size: 15px !important;
    padding: 0.6rem 1rem !important;
    transition: border-color 0.25s, box-shadow 0.25s !important;
}
input[type="number"]:focus, input[type="text"]:focus {
    border-color: #6366f1 !important;
    box-shadow: 0 0 0 3px #6366f120 !important;
    outline: none !important;
}
 
[data-baseweb="select"] > div,
[data-baseweb="select"] > div:hover {
    background: #0f172a !important;
    border: 1px solid #1e293b !important;
    border-radius: 12px !important;
    color: #e2e8f0 !important;
    font-family: 'Epilogue', sans-serif !important;
}
[data-baseweb="select"] svg { fill: #475569 !important; }
[data-baseweb="popover"] { background: #0f172a !important; border: 1px solid #1e293b !important; border-radius: 12px !important; }
[role="option"] { background: #0f172a !important; color: #cbd5e1 !important; font-family: 'Epilogue', sans-serif !important; }
[role="option"]:hover { background: #1e293b !important; }
 
/* Labels */
label[data-testid="stWidgetLabel"] p,
.stNumberInput label, .stTextInput label, .stSelectbox label {
    font-size: 12px !important;
    font-weight: 500 !important;
    letter-spacing: 0.07em !important;
    text-transform: uppercase !important;
    color: #475569 !important;
    margin-bottom: 4px !important;
}
 
/* ── Button ───────────────────────────────────── */
.stButton > button {
    width: 100% !important;
    background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 14px !important;
    padding: 1rem 2rem !important;
    font-family: 'Syne', sans-serif !important;
    font-size: 16px !important;
    font-weight: 700 !important;
    letter-spacing: 0.06em !important;
    text-transform: uppercase !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 0 30px #4f46e530 !important;
    cursor: pointer !important;
}
.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 0 45px #7c3aed55 !important;
    background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%) !important;
}
.stButton > button:active { transform: translateY(0) !important; }
 
/* ── Spinner ──────────────────────────────────── */
[data-testid="stSpinner"] { color: #6366f1 !important; }
 
/* ── Remove default streamlit chrome ─────────── */
#MainMenu, footer, header { visibility: hidden; }
[data-testid="stDecoration"] { display: none; }
</style>
""", unsafe_allow_html=True)
 
# ─────────────────────────────────────────────
#  HERO HEADER
# ─────────────────────────────────────────────
st.markdown("""
<div style="text-align:center; padding: 3rem 0 2.5rem;">
    <div style="display:inline-block; background:#0f172a; border:1px solid #1e293b;
                border-radius:100px; padding:6px 18px; margin-bottom:1.2rem;">
        <span style="font-size:11px; font-weight:600; letter-spacing:0.15em;
                     text-transform:uppercase; color:#6366f1;">AI-Powered · v1.0</span>
    </div>
    <h1 style="font-family:'Syne',sans-serif; font-size:clamp(2.2rem,5vw,3.8rem);
               font-weight:800; color:#f1f5f9; letter-spacing:-0.03em;
               line-height:1.1; margin:0 0 1rem;">
        Insurance Premium
        <span style="background:linear-gradient(90deg,#6366f1,#a78bfa,#38bdf8);
                     -webkit-background-clip:text; -webkit-text-fill-color:transparent;
                     background-clip:text;"> Intelligence</span>
    </h1>
    <p style="font-family:'Epilogue',sans-serif; font-size:1.05rem; color:#64748b;
              max-width:520px; margin:0 auto; font-weight:300; line-height:1.7;">
        Enter your profile below. Our ML model analyses 7 risk factors
        and returns your premium tier with full probability breakdown.
    </p>
</div>
""", unsafe_allow_html=True)
 
# ─────────────────────────────────────────────
#  FORM — two column layout
# ─────────────────────────────────────────────
def glass_header(title, subtitle=""):
    st.markdown(f"""
    <div style="margin: 2rem 0 1rem; padding-bottom: 10px;
                border-bottom: 1px solid #1e293b;">
        <span style="font-family:'Syne',sans-serif; font-size:11px; font-weight:700;
                     letter-spacing:0.15em; text-transform:uppercase; color:#4f46e5;">
            {title}
        </span>
        {"<span style='font-size:12px; color:#334155; margin-left:12px;'>" + subtitle + "</span>" if subtitle else ""}
    </div>
    """, unsafe_allow_html=True)
 
LEFT, RIGHT = st.columns([1.05, 0.95], gap="large")
 
with LEFT:
    # ── Biometric card ──────────────────────────
    st.markdown("""
    <div style="background:#0a1628; border:1px solid #1e293b; border-radius:20px;
                padding:1.8rem 1.8rem 1rem; margin-bottom:1.2rem;">
        <p style="font-family:'Syne',sans-serif; font-size:10px; font-weight:700;
                  letter-spacing:0.18em; text-transform:uppercase; color:#4f46e5;
                  margin:0 0 1.2rem;">
            ◈ &nbsp;Biometric data
        </p>
    """, unsafe_allow_html=True)
 
    b1, b2 = st.columns(2)
    with b1:
        age    = st.number_input("Age (years)", min_value=1, max_value=119, value=30)
        weight = st.number_input("Weight (kg)",  min_value=1.0, step=0.5,   value=70.0)
    with b2:
        height = st.number_input("Height (m)",  min_value=0.5, max_value=2.5, step=0.01, value=1.70)
        city   = st.text_input("City", value="Mumbai", placeholder="Mumbai, Jaipur…")
 
    st.markdown("</div>", unsafe_allow_html=True)
 
    # ── Financial card ──────────────────────────
    st.markdown("""
    <div style="background:#0a1628; border:1px solid #1e293b; border-radius:20px;
                padding:1.8rem 1.8rem 1rem; margin-bottom:1.2rem;">
        <p style="font-family:'Syne',sans-serif; font-size:10px; font-weight:700;
                  letter-spacing:0.18em; text-transform:uppercase; color:#4f46e5;
                  margin:0 0 1.2rem;">
            ◈ &nbsp;Financial profile
        </p>
    """, unsafe_allow_html=True)
 
    f1, f2 = st.columns(2)
    with f1:
        income_lpa = st.number_input("Annual income (LPA)", min_value=0.1, step=0.5, value=10.0)
    with f2:
        occupation = st.selectbox("Occupation", OCCUPATIONS,
                                  format_func=lambda x: x.replace("_", " ").title())
 
    smoker = st.selectbox("Smoking status",
                          options=[False, True],
                          format_func=lambda x: "🚬 Smoker" if x else "🚭 Non-smoker")
 
    st.markdown("</div>", unsafe_allow_html=True)
 
    # ── CTA ─────────────────────────────────────
    predict_clicked = st.button("⚡  Analyse My Premium", type="primary")
 
with RIGHT:
    # ── Live profile preview ─────────────────────
    bmi_live   = get_bmi(weight, height)
    risk_live  = get_lifestyle_risk(smoker, bmi_live)
    ag_live    = get_age_group(age)
    tier_live  = get_city_tier(city)
    bmi_cat, bmi_col = bmi_category(bmi_live)
    risk_pal   = RISK_PALETTE[risk_live]
 
    gauge_svg  = arc_svg(bmi_live, 45, bmi_col, size=170)
 
    st.markdown(f"""
    <div style="background:#0a1628; border:1px solid #1e293b; border-radius:20px;
                padding:1.8rem; margin-bottom:1.2rem; position:relative; overflow:hidden;">
 
      <div style="position:absolute; top:-30px; right:-30px; width:120px; height:120px;
                  background:radial-gradient(circle, {risk_pal['glow']}22 0%, transparent 70%);
                  border-radius:50%;"></div>
 
      <p style="font-family:'Syne',sans-serif; font-size:10px; font-weight:700;
                letter-spacing:0.18em; text-transform:uppercase; color:#4f46e5; margin:0 0 1.4rem;">
          ◈ &nbsp;Live profile preview
      </p>
 
      <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:1.4rem;">
        <div>{gauge_svg}</div>
        <div style="flex:1; padding-left:1.4rem;">
          <div style="font-size:11px; color:#475569; text-transform:uppercase;
                      letter-spacing:0.1em; margin-bottom:4px;">BMI status</div>
          <div style="font-family:'Syne',sans-serif; font-size:22px; font-weight:700;
                      color:{bmi_col};">{bmi_cat}</div>
          <div style="font-size:12px; color:#475569; margin-top:4px;">{bmi_live} kg/m²</div>
        </div>
      </div>
 
      <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px;">
 
        <div style="background:#060e1e; border:1px solid #1e293b; border-radius:12px; padding:12px 14px;">
          <div style="font-size:10px; color:#334155; text-transform:uppercase; letter-spacing:0.1em; margin-bottom:5px;">Lifestyle risk</div>
          <div style="display:flex; align-items:center; gap:6px;">
            <div style="width:8px; height:8px; border-radius:50%; background:{risk_pal['glow']};
                        box-shadow:0 0 6px {risk_pal['glow']};"></div>
            <span style="font-family:'Syne',sans-serif; font-size:14px; font-weight:700;
                         color:{risk_pal['glow']};">{risk_live.upper()}</span>
          </div>
        </div>
 
        <div style="background:#060e1e; border:1px solid #1e293b; border-radius:12px; padding:12px 14px;">
          <div style="font-size:10px; color:#334155; text-transform:uppercase; letter-spacing:0.1em; margin-bottom:5px;">Age group</div>
          <div style="font-family:'Syne',sans-serif; font-size:14px; font-weight:700;
                      color:#a78bfa;">{ag_live.replace('_',' ').title()}</div>
        </div>
 
        <div style="background:#060e1e; border:1px solid #1e293b; border-radius:12px; padding:12px 14px;">
          <div style="font-size:10px; color:#334155; text-transform:uppercase; letter-spacing:0.1em; margin-bottom:5px;">City tier</div>
          <div style="font-family:'Syne',sans-serif; font-size:14px; font-weight:700;
                      color:#38bdf8;">Tier {tier_live} — {city if city else '—'}</div>
        </div>
 
        <div style="background:#060e1e; border:1px solid #1e293b; border-radius:12px; padding:12px 14px;">
          <div style="font-size:10px; color:#334155; text-transform:uppercase; letter-spacing:0.1em; margin-bottom:5px;">Income</div>
          <div style="font-family:'Syne',sans-serif; font-size:14px; font-weight:700;
                      color:#e2e8f0;">₹{income_lpa} LPA</div>
        </div>
 
      </div>
    </div>
 
    <div style="background:#0a1628; border:1px solid #1e293b; border-radius:20px; padding:1.4rem 1.6rem;">
      <p style="font-size:10px; color:#334155; text-transform:uppercase; letter-spacing:0.1em; margin:0 0 10px;">
        How it works
      </p>
      <div style="display:flex; flex-direction:column; gap:8px;">
        {"".join([
            f'<div style="display:flex;align-items:center;gap:10px;">'
            f'<div style="min-width:22px;height:22px;background:#0f172a;border:1px solid #1e293b;'
            f'border-radius:6px;display:flex;align-items:center;justify-content:center;'
            f'font-size:10px;font-weight:700;color:#4f46e5;">{i}</div>'
            f'<span style="font-size:12px;color:#475569;">{t}</span></div>'
            for i, t in [
                ("1", "Your inputs are converted to derived risk features"),
                ("2", "A trained ML pipeline classifies your profile"),
                ("3", "You see the category + full probability breakdown"),
            ]
        ])}
      </div>
    </div>
    """, unsafe_allow_html=True)
 
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
 
        conf_pct = round(confidence * 100, 1)
 
        # ── Hero result banner ──────────────────
        st.markdown(f"""
        <div style="margin-top:2.5rem; background:{pal['grad']};
                    border:1px solid {pal['glow']}40; border-radius:24px;
                    padding:2.5rem 3rem; position:relative; overflow:hidden;">
 
          <div style="position:absolute;top:-60px;right:-60px;width:260px;height:260px;
                      background:radial-gradient(circle,{pal['glow']}20 0%,transparent 65%);
                      border-radius:50%; pointer-events:none;"></div>
          <div style="position:absolute;bottom:-40px;left:-40px;width:200px;height:200px;
                      background:radial-gradient(circle,{pal['glow']}12 0%,transparent 65%);
                      border-radius:50%; pointer-events:none;"></div>
 
          <div style="display:flex; align-items:center; gap:12px; margin-bottom:1rem;">
            <div style="background:{pal['badge_bg']}; border:1px solid {pal['glow']}50;
                        border-radius:100px; padding:5px 16px;">
              <span style="font-size:10px; font-weight:700; letter-spacing:0.15em;
                           text-transform:uppercase; color:{pal['badge_fg']};">
                ● &nbsp;{pal['label']}
              </span>
            </div>
            <div style="background:{pal['badge_bg']}; border:1px solid {pal['glow']}50;
                        border-radius:100px; padding:5px 16px;">
              <span style="font-size:10px; font-weight:700; letter-spacing:0.1em; color:{pal['badge_fg']};">
                CONFIDENCE · {conf_pct}%
              </span>
            </div>
          </div>
 
          <div style="font-family:'Syne',sans-serif; font-size:clamp(2rem,4vw,3.4rem);
                      font-weight:800; color:#f1f5f9; letter-spacing:-0.03em; margin-bottom:0.4rem;">
            {category.title()} Premium
            <span style="color:{pal['glow']};">Category</span>
          </div>
          <p style="font-size:14px; color:#64748b; margin:0; max-width:500px;">
            Based on your biometric, lifestyle and financial profile, our model
            predicts your health insurance falls into the <strong style="color:{pal['accent']};">
            {category} premium</strong> bracket.
          </p>
 
          <div style="margin-top:1.8rem;">
            <div style="font-size:11px; color:#475569; text-transform:uppercase;
                        letter-spacing:0.1em; margin-bottom:8px;">Model confidence</div>
            <div style="height:8px; background:#ffffff15; border-radius:100px; overflow:hidden; max-width:460px;">
              <div style="height:100%; width:{conf_pct}%;
                          background:linear-gradient(90deg,{pal['glow']}80,{pal['glow']});
                          border-radius:100px;"></div>
            </div>
          </div>
 
        </div>
        """, unsafe_allow_html=True)
 
        # ── Breakdown row ───────────────────────
        st.markdown("<div style='margin-top:1.5rem;'>", unsafe_allow_html=True)
        col_prob, col_stats = st.columns([1.1, 0.9], gap="large")
 
        with col_prob:
            st.markdown(f"""
            <div style="background:#0a1628; border:1px solid #1e293b; border-radius:20px;
                        padding:1.8rem; height:100%;">
              <p style="font-family:'Syne',sans-serif; font-size:10px; font-weight:700;
                        letter-spacing:0.18em; text-transform:uppercase; color:#4f46e5; margin:0 0 1.4rem;">
                ◈ &nbsp;Probability breakdown
              </p>
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
            <div style="background:#0a1628; border:1px solid #1e293b; border-radius:20px;
                        padding:1.8rem; height:100%;">
              <p style="font-family:'Syne',sans-serif; font-size:10px; font-weight:700;
                        letter-spacing:0.18em; text-transform:uppercase; color:#4f46e5; margin:0 0 1.4rem;">
                ◈ &nbsp;Risk summary
              </p>
 
              {"".join([
                  f'''<div style="display:flex;align-items:center;justify-content:space-between;
                                 padding:12px 0; border-bottom:1px solid #0f172a;">
                       <span style="font-size:12px;color:#475569;text-transform:uppercase;
                                    letter-spacing:0.07em;">{k}</span>
                       <span style="font-family:'Syne',sans-serif;font-size:13px;
                                    font-weight:700;color:{c};">{v}</span>
                     </div>'''
                  for k, v, c in [
                      ("BMI",           f"{bmi} — {bmi_cat_label}",          bmi_col2),
                      ("Age group",     age_group.replace("_", " ").title(),  "#a78bfa"),
                      ("Lifestyle risk",lifestyle_risk.upper(),                pal["glow"]),
                      ("City tier",     f"Tier {city_tier} · {city}",         "#38bdf8"),
                      ("Income",        f"₹{income_lpa} LPA",                 "#e2e8f0"),
                      ("Occupation",    occupation.replace("_", " ").title(),  "#94a3b8"),
                      ("Smoker",        "Yes" if smoker else "No",             "#f87171" if smoker else "#34d399"),
                  ]
              ])}
            </div>
            """, unsafe_allow_html=True)
 
        st.markdown("</div>", unsafe_allow_html=True)
 
        # ── Footer note ─────────────────────────
        st.markdown(f"""
        <div style="margin-top:1.5rem; text-align:center;">
          <p style="font-size:11px; color:#1e293b;">
            Prediction generated by ML model v1.0.0 · Not financial or medical advice
          </p>
        </div>
        """, unsafe_allow_html=True)
 
    except requests.exceptions.ConnectionError:
        st.error("❌  Cannot reach the FastAPI server on port 8000. Start it with `uvicorn main:app --reload`.")
    except requests.exceptions.Timeout:
        st.error("⏱️  Request timed out after 10 s. Check server health at `/health`.")
    except Exception as e:
        st.error(f"Unexpected error: {e}")
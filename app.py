import streamlit as st
import plotly.graph_objects as go

st.set_page_config(page_title="Australia Fuel Simulator", layout="wide")

col_title, col_shortfall = st.columns([3, 1])
with col_title:
    st.title("🇦🇺 Australia Fuel Supply Chain Simulator")


scenario = st.radio(
    "Select Scenario",
    ["FY25 Business as Normal", 
     "Hormuz Closed (Bab Open) — Analyst Table", 
     "Hormuz + Bab Closed (Worst Case)"],
    horizontal=True
)

# Scenario description (no title)
if scenario == "FY25 Business as Normal":
    st.info("Pre-crisis baseline. Persian Gulf ~27 mbpd total crude, Qatar LNG 77 MTPA.")
elif scenario == "Hormuz Closed (Bab Open) — Analyst Table":
    st.warning("Based on latest analyst table: Gulf crude supply falls from ~27 mbpd to ~13–15 mbpd. "
               "Saudi ~7 mbpd pipeline (5 mbpd export), UAE <1.5 mbpd, Iraq/Kuwait heavily curtailed, "
               "Qatar LNG at zero with 12.8 MTPA destroyed.")
else:
    st.error("Full double chokepoint closure. Persian Gulf supply to Asia near collapse (~0.6–1 mbpd). "
             "Severe shortfall across all fuels.")

# Refinery toggles
st.subheader("Enable / Disable Refining Sources")
cols = st.columns(7)
with cols[0]: sk = st.checkbox("South Korea", value=True)
with cols[1]: sg = st.checkbox("Singapore", value=True)
with cols[2]: my = st.checkbox("Malaysia", value=True)
with cols[3]: ind = st.checkbox("India", value=True)
with cols[4]: cn = st.checkbox("China/Taiwan", value=True)
with cols[5]: us = st.checkbox("US", value=True)
with cols[6]: dom = st.checkbox("Domestic Refineries", value=True)

# Sliders
col1, col2 = st.columns(2)
with col1:
    asia_factor = st.slider("Asia Refinery Output Factor", 0.0, 1.0, 
                            1.0 if "Normal" in scenario else 0.45 if "Bab Open" in scenario else 0.22, 0.05)
with col2:
    dom_factor = st.slider("Domestic Refinery Output Factor", 0.5, 1.0, 1.0, 0.05)

# Demand response
st.subheader("Demand Response / Rationing (100% = Full Demand)")
colA, colB, colC, colD = st.columns(4)
with colA: mining_resp = st.slider("Mining", 0.0, 1.0, 1.0, 0.05)
with colB: transport_resp = st.slider("Transport (Food/Freight)", 0.0, 1.0, 0.85, 0.05)
with colC: agri_resp = st.slider("Agriculture", 0.0, 1.0, 0.90, 0.05)
with colD: domestic_resp = st.slider("Domestic", 0.0, 1.0, 0.80, 0.05)

# Nodes
nodes = [
    "South Korea Refineries", "Singapore Refineries", "Malaysia Refineries", 
    "India Refineries", "China/Taiwan Refineries", "US Refineries", "Domestic Refineries",
    "Oz Diesel Storage", "Oz Petrol Storage", "Oz Avgas Storage",
    "Mining", "Transport", "Agriculture", "Domestic"
]

# Links (adjusted baseline to better reflect analyst table — lower Asia contribution)
links = [
    (0, 7, 0.11), (0, 8, 0.06), (0, 9, 0.02),   # South Korea
    (1, 7, 0.10), (1, 8, 0.07), (1, 9, 0.02),   # Singapore
    (2, 7, 0.06), (2, 8, 0.04), (2, 9, 0.01),   # Malaysia
    (3, 7, 0.04), (3, 8, 0.03), (3, 9, 0.01),   # India
    (4, 7, 0.03), (4, 8, 0.02), (4, 9, 0.02),   # China/Taiwan
    (5, 7, 0.03), (5, 8, 0.02), (5, 9, 0.01),   # US
    (6, 7, 0.13), (6, 8, 0.08), (6, 9, 0.02),   # Domestic
    # Storage → Demand
    (7, 10, 0.05), (7, 11, 0.25), (7, 12, 0.15), (7, 13, 0.05),
    (8, 10, 0.03), (8, 11, 0.15), (8, 12, 0.03), (8, 13, 0.12),
    (9, 10, 0.01), (9, 11, 0.07), (9, 12, 0.00), (9, 13, 0.00)
]

# Apply factors and toggles
adjusted_links = []
for s, t, v in links:
    if s == 0 and not sk: continue
    if s == 1 and not sg: continue
    if s == 2 and not my: continue
    if s == 3 and not ind: continue
    if s == 4 and not cn: continue
    if s == 5 and not us: continue
    if s == 6 and not dom: continue
    
    if t in [7,8,9] and s in [0,1,2,3,4,5]:
        adjusted_links.append((s, t, v * asia_factor))
    elif s == 6:
        adjusted_links.append((s, t, v * dom_factor))
    else:
        adjusted_links.append((s, t, v))

# Apply demand response
final_links = []
for s, t, v in adjusted_links:
    if t == 10: final_links.append((s, t, v * mining_resp))
    elif t == 11: final_links.append((s, t, v * transport_resp))
    elif t == 12: final_links.append((s, t, v * agri_resp))
    elif t == 13: final_links.append((s, t, v * domestic_resp))
    else:
        final_links.append((s, t, v))

# Calculate shortfall %
diesel_supply = sum(v for s,t,v in final_links if t == 7)
petrol_supply = sum(v for s,t,v in final_links if t == 8)
avgas_supply = sum(v for s,t,v in final_links if t == 9)

diesel_short = max(0, round((0.42 - diesel_supply) / 0.42 * 100)) if diesel_supply < 0.42 else 0
petrol_short = max(0, round((0.32 - petrol_supply) / 0.32 * 100)) if petrol_supply < 0.32 else 0
avgas_short = max(0, round((0.12 - avgas_supply) / 0.12 * 100)) if avgas_supply < 0.12 else 0

# Display shortfall
with col_shortfall:
    st.markdown(f"""
    <p style='text-align: right; font-size: 15px; margin-top: 8px;'>
    <strong>Shortfall:</strong> Diesel <strong>{diesel_short}%</strong>, 
    Petrol <strong>{petrol_short}%</strong>, Av Gas <strong>{avgas_short}%</strong>
    </p>
    """, unsafe_allow_html=True)

# Link colors
link_colors = []
for s, t, v in final_links:
    if t in [7,8,9]:
        if t == 7: link_colors.append("rgba(210,166,121,0.85)")
        elif t == 8: link_colors.append("rgba(74,144,226,0.85)")
        else: link_colors.append("rgba(46,139,87,0.85)")
    elif s in [7,8,9]:
        if s == 7: link_colors.append("rgba(210,166,121,0.75)")
        elif s == 8: link_colors.append("rgba(74,144,226,0.75)")
        else: link_colors.append("rgba(46,139,87,0.75)")
    else:
        link_colors.append("rgba(74,44,11,0.85)")

fig = go.Figure(data=[go.Sankey(
    node=dict(
        pad=16,
        thickness=24,
        line=dict(color="black", width=0.5),
        label=nodes,
        color=["#8B5A2B"]*7 + ["#D2A679","#4A90E2","#2E8B57"] + ["#A9A9A9","#555555","#2E8B57","#808080"]
    ),
    link=dict(
        source=[s for s,t,v in final_links],
        target=[t for s,t,v in final_links],
        value=[round(v, 3) for s,t,v in final_links],
        color=link_colors
    )
)])

fig.update_layout(
    title=f"Australia Fuel Supply Chain — {scenario}",
    height=720,
    font=dict(size=15)
)

st.plotly_chart(fig, use_container_width=True)

# Summary
st.subheader("Supply Summary (mbpd)")
col1, col2, col3, col4 = st.columns(4)
total = diesel_supply + petrol_supply + avgas_supply
with col1: st.metric("Diesel", f"{diesel_supply:.2f}")
with col2: st.metric("Petrol", f"{petrol_supply:.2f}")
with col3: st.metric("Avgas", f"{avgas_supply:.2f}")
with col4: st.metric("Total Supply", f"{total:.2f}", delta=f"-{1.1-total:.2f} vs Normal")

st.caption("**Light Brown** = Diesel | **Blue** = Petrol | **Green** = Avgas | Transport includes food & freight priority")

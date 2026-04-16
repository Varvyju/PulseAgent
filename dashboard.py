import streamlit as st
import requests, time

BACKEND = "http://localhost:8000"
st.set_page_config(page_title="PulseAgent", page_icon="🫀", layout="wide")

st.markdown("""
<style>
@keyframes blink { 0%{opacity:1} 50%{opacity:0.5} 100%{opacity:1} }
.critical-box { 
    background: linear-gradient(135deg, #ff000033, #ff000011);
    border: 2px solid #ff4444; border-radius:10px; padding:16px;
    animation: blink 1.2s infinite; text-align:center; font-size:18px; font-weight:bold;
}
.status-bar {
    background: #0d1117; border-radius:8px; padding:8px 16px;
    border: 1px solid #30363d; font-size:12px; color:#8b949e;
}
</style>
""", unsafe_allow_html=True)

# ── HEADER ──
h1, h2, h3 = st.columns([5, 2, 1])
with h1:
    st.markdown("# 🫀 PulseAgent")
    st.caption("Voice: **Vapi** &nbsp;|&nbsp; Memory: **Qdrant** &nbsp;|&nbsp; LLM: **GPT-4o-mini** &nbsp;|&nbsp; Problem: **PS-3 Accessibility & Societal Impact**")
with h2:
    st.markdown(f"### 🕐 {time.strftime('%H:%M:%S')}")
with h3:
    if st.button("🔄 Reset", type="secondary"):
        requests.post(f"{BACKEND}/reset")
        st.rerun()

st.divider()

# ── FETCH STATE ──
try:
    s = requests.get(f"{BACKEND}/state", timeout=2).json()
except Exception as e:
    st.error(f"⚠️ Backend not reachable — run: uvicorn main:app --reload --port 8000")
    st.stop()

urgency = s.get("urgency")

# ── URGENCY BANNER ──
if urgency == "CRITICAL":
    st.markdown('<div class="critical-box">🚨 CRITICAL URGENCY — Immediate Clinical Intervention Required</div>', unsafe_allow_html=True)
    st.markdown("")
elif urgency == "HIGH":
    st.warning("⚠️ HIGH URGENCY — Urgent action needed")
elif urgency == "MODERATE":
    st.info("ℹ️ MODERATE — Monitor patient")

# ── PATIENT INFO ──
st.subheader("👤 Patient Information")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Patient ID", s.get("patient_id") or "—")
c2.metric("Name", s.get("name") or "—")
c3.metric("Age", f"{s.get('age')} yrs" if s.get("age") else "—")
c4.metric("Gender", (s.get("gender") or "—").capitalize())

st.divider()

# ── VITALS ──
st.subheader("📊 Live Vitals")
vitals = s.get("vitals", {})
v1, v2, v3, v4 = st.columns(4)

sys_bp = vitals.get("systolic")
dia_bp = vitals.get("diastolic")
hr = vitals.get("hr")
spo2 = vitals.get("spo2")
temp = vitals.get("temp")

bp_str = f"{sys_bp}/{dia_bp}" if sys_bp else "—"
if sys_bp:
    bp_delta = "🚨 CRITICAL" if int(sys_bp) >= 180 else ("⚠️ ELEVATED" if int(sys_bp) >= 140 else "✅ Normal")
else:
    bp_delta = None

v1.metric("🩸 Blood Pressure", bp_str, delta=bp_delta)
v2.metric("💓 Heart Rate", f"{hr} bpm" if hr else "—",
          delta="⚠️ HIGH" if hr and int(hr) >= 120 else ("✅ Normal" if hr else None))
v3.metric("🫁 SpO2", f"{spo2}%" if spo2 else "—",
          delta="🚨 LOW" if spo2 and int(spo2) < 92 else ("✅ Normal" if spo2 else None))
v4.metric("🌡️ Temperature", f"{temp}°C" if temp else "—")

st.divider()

# ── CLINICAL ASSESSMENT ──
st.subheader("🩺 Clinical Assessment")
left, right = st.columns(2)

with left:
    st.markdown("**Presenting Symptoms**")
    syms = s.get("symptoms", [])
    if syms:
        for sym in syms:
            st.markdown(f"🔸 {sym}")
    else:
        st.markdown("*🎙️ Awaiting voice input...*")

with right:
    st.markdown("**Qdrant Protocol Match**")
    protocol = s.get("protocol")
    if protocol:
        color = "🔴" if urgency == "CRITICAL" else "🟡" if urgency == "HIGH" else "🟢"
        st.success(f"{color} **{protocol.upper().replace('_',' ')}** — retrieved from Qdrant vector search")
    else:
        st.markdown("*Say: \"Check protocols\" to trigger Qdrant RAG*")

# ── ALERTS ──
alerts = s.get("alerts", [])
if alerts:
    st.divider()
    st.subheader("🚨 Active Clinical Alerts")
    for alert in alerts:
        st.error(f"⚠️ {alert}")

# ── PATIENT HISTORY ──
history = s.get("history")
if history:
    st.divider()
    st.subheader("📋 Patient History — Retrieved from Qdrant Memory")
    st.info(f"🗂️ {history}")

# ── FOOTER ──
st.divider()
last = s.get("last_action")
col_l, col_r = st.columns([3, 1])
with col_l:
    if last:
        st.caption(f"⚡ Last agent action: `{last}`")
with col_r:
    status_color = "🟢" if s.get("patient_id") else "🔵"
    st.caption(f"{status_color} System live — auto-refreshing every 2s")

with st.expander("🔧 System Architecture — HackBLR 2026 | Vision_Architect"):
    st.markdown("""
    **Problem Statement:** PS-3 — Voice AI Agent for Accessibility & Societal Impact
    
    | Layer | Technology | Role |
    |-------|-----------|------|
    | Voice | **Vapi** | STT, TTS, Function Calling, Webhook |
    | Memory | **Qdrant Cloud** | RAG over clinical protocols + patient history |
    | Brain | **GPT-4o-mini** | Intent detection, response generation |
    | Backend | **FastAPI** | Webhook handler, state management |
    | Embeddings | **sentence-transformers** | Multilingual semantic search |
    | Dashboard | **Streamlit** | Real-time polling UI |
    
    **Flow:** User speaks → Vapi STT → LLM detects intent → Tool called → FastAPI webhook → Qdrant search → Dashboard updates
    """)

time.sleep(2)
st.rerun()
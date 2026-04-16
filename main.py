from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
from openai import OpenAI
import os, json
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

app = FastAPI(title="PulseAgent")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

qdrant = QdrantClient(url=os.getenv("QDRANT_URL"), api_key=os.getenv("QDRANT_API_KEY"))
embedder = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

# Pre-warm the model so first webhook call isn't slow
print("Pre-warming embedder...")
_ = embedder.encode("warmup query")
print("Embedder ready.")
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Live dashboard state — Streamlit polls this
state = {
    "patient_id": None, "name": None, "age": None, "gender": None,
    "symptoms": [], "vitals": {},
    "alerts": [], "protocol": None, "urgency": None,
    "history": None, "last_action": None
}

def search_qdrant(query: str, collection: str, top_k: int = 2):
    vec = embedder.encode(query).tolist()
    results = qdrant.query_points(
        collection_name=collection,
        query=vec,
        limit=top_k
    ).points
    return [{"text": r.payload.get("text",""), "score": round(r.score, 3), "payload": r.payload} for r in results]

# ── TOOL HANDLERS ──
def handle_log_patient(args):
    # Only update fields that are actually present in args
    if args.get("patient_id"): state["patient_id"] = args["patient_id"]
    if args.get("name"): state["name"] = args["name"]
    if args.get("age"): state["age"] = args["age"]
    if args.get("gender"): state["gender"] = args["gender"]
    if args.get("symptoms"): state["symptoms"] = args["symptoms"]
    state["last_action"] = f"Patient logged at {datetime.now().strftime('%H:%M:%S')}"
    return {"status": "success", "message": f"Patient {state.get('name','recorded')} logged. Dashboard updated."}

def handle_log_vitals(args):
    v = args.get("vitals", {})
    state["vitals"].update(v)
    alerts = []

    sys_bp = v.get("systolic")
    hr = v.get("hr")
    spo2 = v.get("spo2")

    if sys_bp and int(sys_bp) >= 180:
        msg = f"HYPERTENSIVE CRISIS — Systolic {sys_bp}. Immediate action required."
        state["alerts"].append(msg)
        state["urgency"] = "CRITICAL"
        alerts.append(msg)
    if hr and int(hr) >= 120:
        msg = f"TACHYCARDIA — HR {hr} bpm. Monitor closely."
        state["alerts"].append(msg)
        alerts.append(msg)
    if spo2 and int(spo2) < 92:
        msg = f"HYPOXIA — SpO2 {spo2}%. Oxygen required immediately."
        state["alerts"].append(msg)
        state["urgency"] = "CRITICAL"
        alerts.append(msg)

    state["last_action"] = f"Vitals logged at {datetime.now().strftime('%H:%M:%S')}"
    reply = "Vitals logged."
    if alerts:
        reply += " ALERT: " + " | ".join(alerts)
    return {"status": "success", "message": reply, "alerts": alerts}

def handle_query_protocols(args):
    query = args.get("symptoms", "")
    results = search_qdrant(query, "clinical_protocols", top_k=2)

    if not results or results[0]["score"] < 0.35:
        return {"protocol": "No protocol matched with sufficient confidence. Consult attending physician."}

    top = results[0]
    state["protocol"] = top["payload"].get("condition", "unknown")
    state["urgency"] = top["payload"].get("urgency", "unknown").upper()
    state["last_action"] = f"Protocol queried at {datetime.now().strftime('%H:%M:%S')}"

    return {
        "protocol": top["text"],
        "condition": top["payload"].get("condition"),
        "urgency": top["payload"].get("urgency"),
        "confidence_score": top["score"]
    }

def handle_recall_history(args):
    query = args.get("query", "")
    results = search_qdrant(query, "patient_history", top_k=1)

    if not results:
        return {"history": "No patient history found for that query."}

    top = results[0]
    state["history"] = top["text"]
    state["last_action"] = f"History recalled at {datetime.now().strftime('%H:%M:%S')}"
    return {"history": top["text"], "confidence_score": top["score"]}

# ── VAPI WEBHOOK ──
# @app.post("/vapi-webhook")
# async def vapi_webhook(request: Request):
#     body = await request.json()
#     msg = body.get("message", {})
#     msg_type = msg.get("type", "")

#     print(f"\nVapi event: {msg_type}")  # debug log

#     if msg_type == "tool-calls":
#         tool_calls = msg.get("toolCalls", [])
#         results = []
#         for tc in tool_calls:
#             fn = tc["function"]["name"]
#             args = json.loads(tc["function"]["arguments"])
#             print(f"Tool call: {fn} | Args: {args}")

#             if fn == "log_patient_info":
#                 result = handle_log_patient(args)
#             elif fn == "log_vitals":
#                 result = handle_log_vitals(args)
#             elif fn == "query_protocols":
#                 result = handle_query_protocols(args)
#             elif fn == "recall_patient_history":
#                 result = handle_recall_history(args)
#             else:
#                 result = {"error": f"Unknown function: {fn}"}

#             results.append({"toolCallId": tc["id"], "result": json.dumps(result)})
#             print(f"Result: {result}")

#         return {"results": results}

#     return {"status": "ok"}

@app.post("/vapi-webhook")
async def vapi_webhook(request: Request):
    body = await request.json()
    print(f"\n=== FULL BODY ===")
    print(json.dumps(body, indent=2))  # debug — shows exact format
    
    msg = body.get("message", {})
    msg_type = msg.get("type", "")
    print(f"Message type: {msg_type}")

    if msg_type == "tool-calls":
        # Handle BOTH old and new Vapi formats
        tool_calls = msg.get("toolCalls", []) or msg.get("toolCallList", [])
        print(f"Tool calls found: {len(tool_calls)}")
        
        results = []
        for tc in tool_calls:
            try:
                fn_name = tc["function"]["name"]
                raw_args = tc["function"]["arguments"]
                # arguments can be string OR dict depending on Vapi version
                args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
                call_id = tc["id"]
                print(f"Calling: {fn_name} | Args: {args}")

                if fn_name == "log_patient_info":
                    result = handle_log_patient(args)
                elif fn_name == "log_vitals":
                    result = handle_log_vitals(args)
                elif fn_name == "query_protocols":
                    result = handle_query_protocols(args)
                elif fn_name == "recall_patient_history":
                    result = handle_recall_history(args)
                else:
                    result = {"error": f"Unknown function: {fn_name}"}

                print(f"Result: {result}")
                results.append({"toolCallId": call_id, "result": json.dumps(result)})
            
            except Exception as e:
                print(f"ERROR in tool call: {e}")
                results.append({"toolCallId": tc.get("id",""), "result": json.dumps({"error": str(e)})})

        return {"results": results}

    return {"status": "ok"}


# ── STATE ENDPOINTS ──
@app.get("/state")
def get_state():
    return state

@app.post("/reset")
def reset():
    global state
    state = {
        "patient_id": None, "name": None, "age": None, "gender": None,
        "symptoms": [], "vitals": {},
        "alerts": [], "protocol": None, "urgency": None,
        "history": None, "last_action": None
    }
    return {"status": "reset complete"}

@app.get("/health")
def health():
    return {"status": "PulseAgent backend running"}
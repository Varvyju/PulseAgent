from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer
import os
from dotenv import load_dotenv

load_dotenv()

print("Connecting to Qdrant...")
client = QdrantClient(url=os.getenv("QDRANT_URL"), api_key=os.getenv("QDRANT_API_KEY"))
model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
print("Model loaded.")

# Create collections
for col in ["clinical_protocols", "patient_history", "user_memory"]:
    try:
        client.create_collection(col, vectors_config=VectorParams(size=384, distance=Distance.COSINE))
        print(f"Created collection: {col}")
    except:
        print(f"Collection {col} already exists, skipping.")

# Clinical protocols
protocols = [
    {"id": 1, "text": "Acute Coronary Syndrome: Chest pain radiating to left arm or jaw, shortness of breath, sweating, nausea. BP elevated. Action: ECG immediately, aspirin 325mg, call cardiology. Time critical.", "condition": "ACS", "urgency": "critical"},
    {"id": 2, "text": "Hypertensive Crisis: Systolic BP above 180 or diastolic above 120. Severe headache, vision changes, chest pain. Action: IV labetalol, continuous monitoring, reduce BP gradually.", "condition": "hypertensive_crisis", "urgency": "critical"},
    {"id": 3, "text": "Acute Asthma Attack: Wheezing, breathlessness, low SpO2 below 92 percent. Action: Salbutamol nebulizer immediately, oxygen therapy, IV hydrocortisone. Avoid beta blockers.", "condition": "asthma_attack", "urgency": "high"},
    {"id": 4, "text": "Sepsis: Fever above 38 or below 36, heart rate above 90, respiratory rate above 20, suspected infection. Action: Blood cultures, broad spectrum antibiotics within 1 hour, IV fluids 30ml per kg.", "condition": "sepsis", "urgency": "critical"},
    {"id": 5, "text": "Stroke: Sudden facial droop, arm weakness, slurred speech. FAST protocol. tPA window 4.5 hours. Immediate CT scan. Do not give anticoagulants before imaging.", "condition": "stroke", "urgency": "critical"},
    {"id": 6, "text": "Diabetic Ketoacidosis: Blood sugar above 250, ketones in urine, Kussmaul breathing, fruity breath. Action: IV fluid resuscitation, insulin drip, potassium monitoring.", "condition": "DKA", "urgency": "high"},
    {"id": 7, "text": "Anaphylaxis: Rapid hives or swelling, airway compromise, hypotension after allergen exposure. Action: Epinephrine 0.3mg IM into thigh immediately. Antihistamines secondary. Monitor for biphasic reaction.", "condition": "anaphylaxis", "urgency": "critical"},
    {"id": 8, "text": "Pneumonia: Fever, productive cough, chest pain on breathing, decreased breath sounds. Action: Chest X-ray, sputum culture, empirical antibiotics amoxicillin or azithromycin. Check oxygen saturation.", "condition": "pneumonia", "urgency": "moderate"},
]

points = [PointStruct(id=p["id"], vector=model.encode(p["text"]).tolist(),
          payload={"text": p["text"], "condition": p["condition"], "urgency": p["urgency"]}) for p in protocols]
client.upsert("clinical_protocols", points=points)
print(f"Seeded {len(points)} clinical protocols.")

# Patient history
patients = [
    {"id": 201, "text": "Patient ID 101, Ravi Kumar, 58 years old male. Known hypertension on amlodipine 5mg. Type 2 diabetes on metformin. Allergic to penicillin. Last visit 2 months ago for chest discomfort.", "patient_id": "101", "name": "Ravi Kumar"},
    {"id": 202, "text": "Patient ID 102, Sunita Devi, 45 years old female. Severe asthma, uses salbutamol inhaler daily. No known drug allergies. Two prior hospitalizations for asthma attacks.", "patient_id": "102", "name": "Sunita Devi"},
    {"id": 203, "text": "Patient ID 103, Mohammed Iqbal, 67 years old male. Chronic smoker, COPD diagnosed 2020. On tiotropium. History of ischemic stroke 3 years ago. On aspirin 75mg daily.", "patient_id": "103", "name": "Mohammed Iqbal"},
    {"id": 204, "text": "Patient ID 104, Lakshmi Bai, 52 years old female. Type 1 diabetes, insulin dependent. Hypertension. History of DKA admission last year. Allergic to sulfa drugs.", "patient_id": "104", "name": "Lakshmi Bai"},
]

p_points = [PointStruct(id=p["id"], vector=model.encode(p["text"]).tolist(),
            payload={"text": p["text"], "patient_id": p["patient_id"], "name": p["name"]}) for p in patients]
client.upsert("patient_history", points=p_points)
print(f"Seeded {len(p_points)} patient records.")

print("\nQdrant ready. All collections seeded successfully.")
print(f"Cluster: {os.getenv('QDRANT_URL')}")
import json
import os
import time
from datetime import datetime

# -----------------------------
# CONFIG
# -----------------------------
BASE_DIR = os.path.dirname(__file__)
INPUT_FILE = os.path.join(BASE_DIR, "allergy_panel.json")

OUTPUT_MOD = os.path.join(BASE_DIR, "output.mod")
OUTPUT_NQ = os.path.join(BASE_DIR, "output.nq")

# -----------------------------
# LOAD JSON
# -----------------------------
with open(INPUT_FILE, "r", encoding="utf-8") as f:
    workflow = json.load(f)

states = workflow["states"]

# -----------------------------
# HELPERS
# -----------------------------
def now_ts():
    return int(time.time())

def event_uri(line_id):
    return f"<http://example.org/event/Line_{line_id}>"

def snomed_uri(code):
    return f"<http://snomed.info/id/{code}>"

# -----------------------------
# OUTPUT BUFFERS
# -----------------------------
mod_lines = []
nq_lines = []

line_id = 1
current_state = "Initial"
visited = set()

# -----------------------------
# HEADER MOD
# -----------------------------
mod_lines.append("aActivity,nTimestamp,aActor,aActionType,sModelReference,sSnomed")

# -----------------------------
# MAIN LOOP
# -----------------------------
while current_state in states and current_state not in visited:
    visited.add(current_state)
    state = states[current_state]

    ts = now_ts()
    event = event_uri(line_id)

    actor = "System"
    action_type = "at_" + state.get("type", "Unknown")

    model_ref = f"http://example.org/model/{current_state}"

    # -----------------------------
    # SNOMED extraction
    # -----------------------------
    snomed = None

    if "codes" in state:
        for c in state["codes"]:
            if c.get("system") in ["SNOMED-CT", "SNOMED"]:
                snomed = snomed_uri(c["code"])
                break

    if snomed is None:
        snomed = "http://snomed.info/id/0"

    # -----------------------------
    # MOD LINE (UNCHANGED STRUCTURE)
    # -----------------------------
    mod_lines.append(
        f"{current_state},{current_state}&{ts}&{actor}&{action_type}&{snomed}&{event}"
    )

    # -----------------------------
    # CORE RDF (TU ORIGINAL)
    # -----------------------------
    nq_lines.append(
        f"<http://example.org/case/{current_state}> "
        f"<http://snomed.info/snomed#undergoes> "
        f"<http://example.org/procedure/{current_state}> {event} ."
    )

    nq_lines.append(
        f"<http://example.org/procedure/{current_state}> "
        f"<http://www.w3.org/1999/02/22-rdf-syntax-ns#type> "
        f"<{snomed_uri(state['codes'][0]['code']) if 'codes' in state else snomed}> {event} ."
    )

    nq_lines.append(
        f"<http://example.org/procedure/{current_state}> "
        f"<http://snomed.info/snomed#evaluationMethod> "
        f"\"Automated_generated\" {event} ."
    )

    # =========================================================
    # 🔥 ENRICHED RDF LAYER (NUEVO SIN ROMPER TU CÓDIGO)
    # =========================================================

    base_proc = f"<http://example.org/procedure/{current_state}>"
    base_case = f"<http://example.org/case/{current_state}>"

    # --- temporal / identity ---
    nq_lines.append(f"{base_proc} <http://example.org/hasTimestamp> \"{ts}\" {event} .")
    nq_lines.append(f"{base_proc} <http://example.org/generatedAt> \"{datetime.utcnow().isoformat()}\" {event} .")

    # --- semantics ---
    nq_lines.append(f"{base_proc} <http://www.w3.org/2000/01/rdf-schema#label> \"{current_state}\" {event} .")
    nq_lines.append(f"{base_proc} <http://example.org/stateType> \"{state.get('type','Unknown')}\" {event} .")

    # --- SNOMED enrichment ---
    if "codes" in state:
        for i, c in enumerate(state["codes"][:5]):
            nq_lines.append(
                f"{base_proc} <http://example.org/snomedCode_{i}> \"{c.get('code','')}\" {event} ."
            )
            nq_lines.append(
                f"{base_proc} <http://example.org/snomedSystem_{i}> \"{c.get('system','')}\" {event} ."
            )
            nq_lines.append(
                f"{base_proc} <http://example.org/snomedDisplay_{i}> \"{c.get('display','')}\" {event} ."
            )

    # --- case linking ---
    nq_lines.append(f"{base_case} <http://example.org/hasProcedure> {base_proc} {event} .")
    nq_lines.append(f"{base_proc} <http://example.org/belongsToCase> {base_case} {event} .")

    # --- reasoning hooks ---
    nq_lines.append(f"{base_proc} <http://example.org/isSynthetic> \"true\" {event} .")
    nq_lines.append(f"{base_proc} <http://example.org/sourceSystem> \"Synthea\" {event} .")

    # --- temporal index (clave para LTL luego) ---
    nq_lines.append(f"{base_proc} <http://example.org/temporalIndex> \"{line_id}\" {event} .")

    # -----------------------------
    # TRANSITION LOGIC (TU ORIGINAL)
    # -----------------------------
    next_state = None

    if "direct_transition" in state:
        next_state = state["direct_transition"]

    elif "conditional_transition" in state:
        transitions = state["conditional_transition"]
        next_state = transitions[-1]["transition"]

        for t in transitions:
            cond = t.get("condition")
            if cond:
                for c in cond.get("codes", []):
                    nq_lines.append(
                        f"<{snomed_uri(c['code'])}> "
                        f"<http://snomed.info/snomed#conditionCode> "
                        f"\"{c['code']}\" {event} ."
                    )

    else:
        next_state = None

    # -----------------------------
    # ADVANCE
    # -----------------------------
    current_state = next_state
    line_id += 1

# -----------------------------
# WRITE FILES
# -----------------------------
with open(OUTPUT_MOD, "w", encoding="utf-8") as f:
    f.write("\n".join(mod_lines))

with open(OUTPUT_NQ, "w", encoding="utf-8") as f:
    f.write("\n".join(nq_lines))

print("✔ DONE")
print("MOD:", OUTPUT_MOD)
print("NQ :", OUTPUT_NQ)
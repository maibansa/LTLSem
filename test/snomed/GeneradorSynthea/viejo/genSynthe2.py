import json
import os
import time
import uuid
from datetime import datetime

# -----------------------------
# CONFIG
# -----------------------------
BASE_DIR = os.path.dirname(__file__)
INPUT_FILE = os.path.join(BASE_DIR, "allergy_panel.json")

OUTPUT_MOD = os.path.join(BASE_DIR, "output.mod")
OUTPUT_NQ = os.path.join(BASE_DIR, "output.nq")

NUM_TRACES = 10

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

def event_uri(trace_id, line_id):
    return f"<http://example.org/event/{trace_id}_Line_{line_id}>"

def snomed_uri(code):
    return f"<http://snomed.info/id/{code}>"

# -----------------------------
# OUTPUT BUFFERS
# -----------------------------
mod_lines = []
nq_lines = []

# -----------------------------
# HEADER MOD
# -----------------------------
mod_lines.append("traceId,aActivity,nTimestamp,aActor,aActionType,sModelReference,sSnomed")

# -----------------------------
# MULTI-TRACE EXECUTION
# -----------------------------
for t in range(NUM_TRACES):

    # 🔥 FIX: IDs distintos por traza (ESTO ES LO ÚNICO CAMBIADO)
    trace_id = f"allergy_panel_{t+1}"

    line_id = 1
    current_state = "Initial"
    visited = set()

    while current_state in states and current_state not in visited:
        visited.add(current_state)
        state = states[current_state]

        ts = now_ts()
        event = event_uri(trace_id, line_id)

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
        # MOD LINE (UNCHANGED)
        # -----------------------------
        mod_lines.append(
            f"{trace_id},"
            f"{current_state},"
            f"{ts}&{actor}&{action_type}&{model_ref}&{snomed}&{event}"
        )

        # -----------------------------
        # CORE RDF (UNCHANGED)
        # -----------------------------
        nq_lines.append(
            f"<http://example.org/case/{trace_id}> "
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

        # -----------------------------
        # ENRICHMENT (UNCHANGED)
        # -----------------------------
        base_proc = f"<http://example.org/procedure/{current_state}>"
        base_case = f"<http://example.org/case/{trace_id}>"

        nq_lines.append(f"{base_proc} <http://example.org/hasTimestamp> \"{ts}\" {event} .")
        nq_lines.append(f"{base_proc} <http://example.org/generatedAt> \"{datetime.utcnow().isoformat()}\" {event} .")

        nq_lines.append(f"{base_proc} <http://www.w3.org/2000/01/rdf-schema#label> \"{current_state}\" {event} .")
        nq_lines.append(f"{base_proc} <http://example.org/stateType> \"{state.get('type','Unknown')}\" {event} .")

        if "codes" in state:
            for i, c in enumerate(state["codes"][:5]):
                nq_lines.append(
                    f"{base_proc} <http://example.org/snomedCode_{i}> \"{c.get('code','')}\" {event} ."
                )

        nq_lines.append(f"{base_case} <http://example.org/hasProcedure> {base_proc} {event} .")
        nq_lines.append(f"{base_proc} <http://example.org/belongsToCase> {base_case} {event} .")

        nq_lines.append(f"{base_proc} <http://example.org/isSynthetic> \"true\" {event} .")
        nq_lines.append(f"{base_proc} <http://example.org/sourceSystem> \"Synthea\" {event} .")

        nq_lines.append(f"{base_proc} <http://example.org/temporalIndex> \"{line_id}\" {event} .")

        # -----------------------------
        # TRANSITION (UNCHANGED)
        # -----------------------------
        if "direct_transition" in state:
            next_state = state["direct_transition"]

        elif "conditional_transition" in state:
            transitions = state["conditional_transition"]
            next_state = transitions[-1]["transition"]

        else:
            next_state = None

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
print("TRACES:", NUM_TRACES)
print("MOD:", OUTPUT_MOD)
print("NQ :", OUTPUT_NQ)
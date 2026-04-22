import json
import os
import time
import random
from datetime import datetime

# -----------------------------
# CONFIG
# -----------------------------
BASE_DIR = os.path.dirname(__file__)

WORKFLOWS = [
    "allergies.json",
    "appendicitis.json",
    "asthma.json",
    "breast_cancer.json",
    "colorectal_cancer.json",
    "copd.json",
    "dermatitis.json",
    "ear_infections.json",
    "epilepsy.json",
    "fibromyalgia.json"
]

NUM_TRACES = 10

MIN_STEPS = 15     # 🔥 FIX: fuerza trazas útiles
MAX_STEPS = 40

OUTPUT_MOD = os.path.join(BASE_DIR, "output.mod")
OUTPUT_NQ = os.path.join(BASE_DIR, "output.nq")

# -----------------------------
# HELPERS
# -----------------------------
def now_ts():
    return int(time.time())

def event_uri(trace_id, line_id):
    return f"<http://example.org/event/{trace_id}_Line_{line_id}>"

def snomed_uri(code):
    return f"<http://snomed.info/id/{code}>"

def safe_next_state(state):
    """
    Manejo robusto de transiciones:
    - si no hay transición → self-loop controlado
    """
    if "direct_transition" in state:
        return state["direct_transition"]

    if "conditional_transition" in state:
        return random.choice(state["conditional_transition"])["transition"]

    return None

# -----------------------------
# OUTPUT
# -----------------------------
mod_lines = []
nq_lines = []

mod_lines.append("traceId,aActivity,nTimestamp,aActor,aActionType,sModelReference,sSnomed")

# -----------------------------
# MAIN LOOP
# -----------------------------
for wf_name in WORKFLOWS:

    input_file = os.path.join(BASE_DIR, wf_name)

    with open(input_file, "r", encoding="utf-8") as f:
        workflow = json.load(f)

    states = workflow["states"]

    for t in range(NUM_TRACES):

        trace_id = f"{wf_name.replace('.json','')}_trace_{t+1}"

        line_id = 1
        current_state = "Initial"

        # 🔥 FIX: control de longitud fija
        steps = 0
        max_steps_trace = random.randint(MIN_STEPS, MAX_STEPS)

        while steps < max_steps_trace:

            # 🔥 si estado inválido → forzar estado terminal estable
            if current_state not in states:
                current_state = random.choice(list(states.keys()))

            state = states[current_state]

            ts = now_ts()
            event = event_uri(trace_id, line_id)

            actor = "System"
            action_type = "at_" + state.get("type", "Unknown")

            model_ref = f"http://example.org/model/{current_state}"

            # -----------------------------
            # SNOMED
            # -----------------------------
            snomed = "http://snomed.info/id/0"

            if "codes" in state:
                for c in state["codes"]:
                    if c.get("system") in ["SNOMED-CT", "SNOMED"]:
                        snomed = snomed_uri(c["code"])
                        break

            # -----------------------------
            # MOD
            # -----------------------------
            mod_lines.append(
                f"{trace_id},"
                f"{current_state},"
                f"{ts}&{actor}&{action_type}&{model_ref}&{snomed}&{event}"
            )

            # -----------------------------
            # RDF CORE
            # -----------------------------
            base_proc = f"<http://example.org/procedure/{current_state}>"
            base_case = f"<http://example.org/case/{trace_id}>"

            nq_lines.append(
                f"{base_case} <http://snomed.info/snomed#undergoes> {base_proc} {event} ."
            )

            nq_lines.append(
                f"{base_proc} <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> "
                f"<{snomed}> {event} ."
            )

            nq_lines.append(
                f"{base_proc} <http://example.org/stateType> "
                f"\"{state.get('type','Unknown')}\" {event} ."
            )

            nq_lines.append(
                f"{base_proc} <http://example.org/temporalIndex> "
                f"\"{line_id}\" {event} ."
            )

            nq_lines.append(
                f"{base_proc} <http://example.org/isSynthetic> \"true\" {event} ."
            )

            # -----------------------------
            # NEXT STATE
            # -----------------------------
            next_state = safe_next_state(state)

            if next_state is None:
                # 🔥 FIX: self-loop controlado (evita trazas cortas)
                next_state = current_state

            current_state = next_state

            line_id += 1
            steps += 1

# -----------------------------
# WRITE
# -----------------------------
with open(OUTPUT_MOD, "w", encoding="utf-8") as f:
    f.write("\n".join(mod_lines))

with open(OUTPUT_NQ, "w", encoding="utf-8") as f:
    f.write("\n".join(nq_lines))

print("✔ DONE (FIXED BENCHMARK)")
print("WORKFLOWS:", len(WORKFLOWS))
print("TRACES PER WORKFLOW:", NUM_TRACES)
print("MIN/MAX STEPS:", MIN_STEPS, MAX_STEPS)
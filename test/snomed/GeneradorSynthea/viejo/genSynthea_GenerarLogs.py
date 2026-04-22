import json
import os
import random
import time
from pathlib import Path

# -----------------------------
# CONFIGURACIÓN DE RUTAS Y RANGOS
# -----------------------------
BASE_DIR = os.path.dirname(__file__)
AUTO_DIR = os.path.join(BASE_DIR, "auto")

# Crear la carpeta 'auto' si no existe
if not os.path.exists(AUTO_DIR):
    os.makedirs(AUTO_DIR)

WORKFLOWS = [
    "allergies.json", "appendicitis.json", "asthma.json",
    "breast_cancer.json", "colorectal_cancer.json", "copd.json",
    "dermatitis.json", "ear_infections.json", "epilepsy.json",
    "fibromyalgia.json"
]

# Definición de los experimentos solicitados
LISTA_NUM_TRACES = [50, 100, 500, 1000, 5000, 10000]
RANGOS_PASOS = [
    (6, 20), (21, 35), (36, 50), (51, 65), (66, 80)
]

# -----------------------------
# HELPERS SEMÁNTICOS
# -----------------------------
def snomed_uri(code): return f"<http://snomed.info/id/{code}>"
def clean(txt): return str(txt).replace(" ", "_").replace('"', "").replace("'", "").replace("\n", " ")

def get_deep_semantics(state_name, state_data, event_uri, wf_name):
    q = []
    proc_uri = f"<http://example.org/procedure/{wf_name}/{clean(state_name)}>"
    q.append(f"{proc_uri} <http://www.w3.org/2000/01/rdf-schema#label> \"{clean(state_name)}\" {event_uri} .")
    st_type = state_data.get("type", "State")
    q.append(f"{proc_uri} <http://example.org/ontology/hasStateType> \"{st_type}\" {event_uri} .")

    codes = list(state_data.get("codes", []))
    if "activities" in state_data:
        for act in state_data["activities"]:
            codes.extend(act.get("codes", []))
    
    for c in codes:
        sys = clean(c.get("system", "unknown"))
        code = clean(c.get("code", "0"))
        label = clean(c.get("display", "N/A"))
        c_uri = snomed_uri(code) if "SNOMED" in sys.upper() else f"<http://example.org/code/{sys}/{code}>"
        q.append(f"{proc_uri} <http://example.org/ontology/clinicalCode> {c_uri} {event_uri} .")
        q.append(f"{c_uri} <http://www.w3.org/2000/01/rdf-schema#label> \"{label}\" {event_uri} .")

    if "allow" in state_data:
        allow = state_data["allow"]
        q.append(f"{proc_uri} <http://example.org/ontology/gateCondition> \"{allow.get('condition_type')}\" {event_uri} .")
        if "attribute" in allow:
            q.append(f"{proc_uri} <http://example.org/ontology/monitorsAttribute> \"{allow['attribute']}\" {event_uri} .")
    
    if "submodule" in state_data:
        q.append(f"{proc_uri} <http://example.org/ontology/externalModule> \"{state_data['submodule']}\" {event_uri} .")
    if "encounter_class" in state_data:
        q.append(f"{proc_uri} <http://example.org/ontology/encounterClass> \"{state_data['encounter_class']}\" {event_uri} .")

    return q

# -----------------------------
# EJECUCIÓN POR EXPERIMENTO
# -----------------------------

for num_traces in LISTA_NUM_TRACES:
    for min_steps, max_steps in RANGOS_PASOS:
        
        # Nombre de archivo solicitado: log_NUM_TRACES_MIN_STEPS_MAX_STEPS
        base_filename = f"log_{num_traces}_{min_steps}_{max_steps}"
        output_mod = os.path.join(AUTO_DIR, f"{base_filename}.mod")
        output_nq = os.path.join(AUTO_DIR, f"{base_filename}.nq")
        
        mod_lines = ["aActivity,nTimestamp,aActor,aActionType,sModelReference,sSnomed,aWorkflow"]
        nq_lines = []

        print(f"Procesando: {base_filename}...")

        for wf_file in WORKFLOWS:
            path = os.path.join(BASE_DIR, wf_file)
            if not os.path.exists(path):
                continue
            
            with open(path, "r", encoding="utf-8") as f:
                wf_json = json.load(f)
            
            wf_name = Path(wf_file).stem
            states = wf_json["states"]

            for t_idx in range(num_traces):
                trace_id = f"{wf_name}_trace_{t_idx+1}"
                case_uri = f"<http://example.org/case/{trace_id}>"
                curr_state = "Initial"
                line_id = 1
                steps = 0
                # Se decide el máximo de pasos para esta traza específica dentro del rango
                limit_steps = random.randint(min_steps, max_steps)

                while steps < limit_steps:
                    if curr_state not in states: break
                    
                    st_data = states[curr_state]
                    event_uri = f"<http://example.org/event/{trace_id}_L{line_id}>"
                    proc_uri = f"<http://example.org/procedure/{wf_name}/{clean(curr_state)}>"
                    ts = int(time.time()) + (line_id * 10)

                    # --- GENERAR MOD ---
                    first_snomed = "0"
                    for c in st_data.get("codes", []):
                        if "SNOMED" in c.get("system", "").upper():
                            first_snomed = c["code"]
                            break
                    
                    mod_lines.append(f"{trace_id},{curr_state}&{ts}&System&at_{st_data.get('type')}&{snomed_uri(first_snomed)}&{event_uri}&{wf_name}")

                    # --- GENERAR NQ ---
                    nq_lines.append(f"{case_uri} <http://example.org/ontology/hasEvent> {event_uri} {event_uri} .")
                    nq_lines.append(f"{event_uri} <http://example.org/ontology/executes> {proc_uri} {event_uri} .")
                    nq_lines.extend(get_deep_semantics(curr_state, st_data, event_uri, wf_name))
                    
                    if line_id > 1:
                        prev_event = f"<http://example.org/event/{trace_id}_L{line_id-1}>"
                        nq_lines.append(f"{event_uri} <http://example.org/ontology/follows> {prev_event} {event_uri} .")

                    # --- TRANSICIÓN ---
                    if "direct_transition" in st_data:
                        next_s = st_data["direct_transition"]
                    elif "conditional_transition" in st_data:
                        next_s = random.choice(st_data["conditional_transition"])["transition"]
                    else:
                        break
                    
                    curr_state = next_s
                    line_id += 1
                    steps += 1

        # Escritura de los archivos finales del experimento actual
        with open(output_mod, "w", encoding="utf-8") as f:
            f.write("\n".join(mod_lines))

        with open(output_nq, "w", encoding="utf-8") as f:
            f.write("\n".join(nq_lines))

print(f"\n✔ Proceso finalizado. Revisa la carpeta: {AUTO_DIR}")
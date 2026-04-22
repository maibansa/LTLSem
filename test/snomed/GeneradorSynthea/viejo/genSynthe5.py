import json
import os
import random
import time
from pathlib import Path

# -----------------------------
# CONFIGURACIÓN SOLICITADA
# -----------------------------
BASE_DIR = os.path.dirname(__file__)

WORKFLOWS = [
    "allergies.json", "appendicitis.json", "asthma.json",
    "breast_cancer.json", "colorectal_cancer.json", "copd.json",
    "dermatitis.json", "ear_infections.json", "epilepsy.json",
    "fibromyalgia.json"
]

NUM_TRACES = 1000
MIN_STEPS = 5
MAX_STEPS = 20

OUTPUT_MOD = os.path.join(BASE_DIR, "output_10000_5_20.mod")
OUTPUT_NQ = os.path.join(BASE_DIR, "output_10000_5_20.nq")

# -----------------------------
# HELPERS SEMÁNTICOS
# -----------------------------
def snomed_uri(code): return f"<http://snomed.info/id/{code}>"
def clean(txt): return str(txt).replace(" ", "_").replace('"', "").replace("'", "").replace("\n", " ")

def get_deep_semantics(state_name, state_data, event_uri, wf_name):
    """Extrae metadatos profundos del estado para el archivo .nq"""
    q = []
    # URI del Proceso (Clase abstracta en el workflow)
    proc_uri = f"<http://example.org/procedure/{wf_name}/{clean(state_name)}>"
    
    # 1. Identidad y Tipo
    q.append(f"{proc_uri} <http://www.w3.org/2000/01/rdf-schema#label> \"{clean(state_name)}\" {event_uri} .")
    st_type = state_data.get("type", "State")
    q.append(f"{proc_uri} <http://example.org/ontology/hasStateType> \"{st_type}\" {event_uri} .")

    # 2. Extracción de Códigos Médicos y Etiquetas (SNOMED / RxNorm / LOINC)
    codes = list(state_data.get("codes", []))
    if "activities" in state_data: # Típico de CarePlan
        for act in state_data["activities"]:
            codes.extend(act.get("codes", []))
    
    for c in codes:
        sys = clean(c.get("system", "unknown"))
        code = clean(c.get("code", "0"))
        label = clean(c.get("display", "N/A"))
        c_uri = snomed_uri(code) if "SNOMED" in sys.upper() else f"<http://example.org/code/{sys}/{code}>"
        
        q.append(f"{proc_uri} <http://example.org/ontology/clinicalCode> {c_uri} {event_uri} .")
        q.append(f"{c_uri} <http://www.w3.org/2000/01/rdf-schema#label> \"{label}\" {event_uri} .")

    # 3. Lógica de Decisión (Atributos, Edades, Condiciones)
    # Extraemos qué está "vigilando" el workflow en este paso
    if "allow" in state_data:
        allow = state_data["allow"]
        q.append(f"{proc_uri} <http://example.org/ontology/gateCondition> \"{allow.get('condition_type')}\" {event_uri} .")
        if "attribute" in allow:
            q.append(f"{proc_uri} <http://example.org/ontology/monitorsAttribute> \"{allow['attribute']}\" {event_uri} .")
    
    # 4. Metadatos de Negocio (Submódulos y Encuentros)
    if "submodule" in state_data:
        q.append(f"{proc_uri} <http://example.org/ontology/externalModule> \"{state_data['submodule']}\" {event_uri} .")
    if "encounter_class" in state_data:
        q.append(f"{proc_uri} <http://example.org/ontology/encounterClass> \"{state_data['encounter_class']}\" {event_uri} .")

    return q

# -----------------------------
# BUCLE DE GENERACIÓN
# -----------------------------
mod_lines = ["aActivity,nTimestamp,aActor,aActionType,sModelReference,sSnomed,aWorkflow"]
nq_lines = []

for wf_file in WORKFLOWS:
    path = os.path.join(BASE_DIR, wf_file)
    if not os.path.exists(path):
        print(f"⚠ Saltando {wf_file}: No encontrado.")
        continue
    
    with open(path, "r", encoding="utf-8") as f:
        wf_json = json.load(f)
    
    wf_name = Path(wf_file).stem
    states = wf_json["states"]

    for t_idx in range(NUM_TRACES):
        trace_id = f"{wf_name}_trace_{t_idx+1}"
        case_uri = f"<http://example.org/case/{trace_id}>"
        curr_state = "Initial"
        line_id = 1
        steps = 0
        max_steps = random.randint(MIN_STEPS, MAX_STEPS)

        while steps < max_steps:
            if curr_state not in states: break
            
            st_data = states[curr_state]
            event_uri = f"<http://example.org/event/{trace_id}_L{line_id}>"
            proc_uri = f"<http://example.org/procedure/{wf_name}/{clean(curr_state)}>"
            ts = int(time.time()) + (line_id * 10) # Simular avance temporal

            # --- GENERAR MOD ---
            # Intentamos sacar un SNOMED para la columna sSnomed del MOD
            first_snomed = "0"
            for c in st_data.get("codes", []):
                if "SNOMED" in c.get("system", "").upper():
                    first_snomed = c["code"]
                    break
            
            mod_lines.append(f"{trace_id},{curr_state}&{ts}&System&at_{st_data.get('type')}&{snomed_uri(first_snomed)}&{event_uri}&{wf_name}")

            # --- GENERAR NQ (Semántica Rica) ---
            nq_lines.append(f"{case_uri} <http://example.org/ontology/hasEvent> {event_uri} {event_uri} .")
            nq_lines.append(f"{event_uri} <http://example.org/ontology/executes> {proc_uri} {event_uri} .")
            
            # Inyección de metadatos profundos
            nq_lines.extend(get_deep_semantics(curr_state, st_data, event_uri, wf_name))
            
            # Relación temporal con el evento anterior
            if line_id > 1:
                prev_event = f"<http://example.org/event/{trace_id}_L{line_id-1}>"
                nq_lines.append(f"{event_uri} <http://example.org/ontology/follows> {prev_event} {event_uri} .")

            # --- TRANSICIÓN ---
            if "direct_transition" in st_data:
                next_s = st_data["direct_transition"]
            elif "conditional_transition" in st_data:
                # Simplificado: elegimos una al azar para la simulación
                next_s = random.choice(st_data["conditional_transition"])["transition"]
            else:
                break
            
            curr_state = next_s
            line_id += 1
            steps += 1

# -----------------------------
# ESCRITURA DE ARCHIVOS
# -----------------------------
with open(OUTPUT_MOD, "w", encoding="utf-8") as f:
    f.write("\n".join(mod_lines))

with open(OUTPUT_NQ, "w", encoding="utf-8") as f:
    f.write("\n".join(nq_lines))

print(f"✔ Proceso finalizado.")
print(f"- Trazas generadas: {len(WORKFLOWS) * NUM_TRACES}")
print(f"- Archivos: {OUTPUT_MOD} y {OUTPUT_NQ}")
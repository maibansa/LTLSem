import json
import os
import random
import time
from pathlib import Path

# -----------------------------
# CONFIGURACIÓN
# -----------------------------
BASE_DIR = os.path.dirname(__file__)
AUTO_DIR = os.path.join(BASE_DIR, "auto")
if not os.path.exists(AUTO_DIR): os.makedirs(AUTO_DIR)

WORKFLOWS = [
    "allergies.json", "appendicitis.json", "asthma.json",
    "breast_cancer.json", "colorectal_cancer.json", "copd.json",
    "dermatitis.json", "ear_infections.json", "epilepsy.json",
    "fibromyalgia.json"
]

LISTA_NUM_TRACES = (100,)
RANGOS_PASOS = ((61, 80),)

def snomed_uri(code): return f"<http://snomed.info/id/{code}>"
def clean(txt): return str(txt).replace(" ", "_").replace('"', "").replace("'", "").replace("\n", " ")

# -----------------------------
# EJECUCIÓN
# -----------------------------

for num_traces in LISTA_NUM_TRACES:
    for min_steps, max_steps in RANGOS_PASOS:
        base_filename = f"log_{num_traces*len(WORKFLOWS)}_{min_steps}_{max_steps}"
        output_mod = os.path.join(AUTO_DIR, f"{base_filename}.mod")
        
        # Cabecera CSV para el Model Checker
        mod_lines = ["aActivity,nTimestamp,aActor,aActionType,sModelReference,sSnomed,aWorkflow"]

        for wf_file in WORKFLOWS:
            path = os.path.join(BASE_DIR, wf_file)
            if not os.path.exists(path): continue
            with open(path, "r", encoding="utf-8") as f: wf_json = json.load(f)
            
            wf_name = Path(wf_file).stem
            states = wf_json["states"]

            for t_idx in range(num_traces):
                trace_id = f"{wf_name}_trace_{t_idx+1}"
                curr_state = "Initial"
                line_id = 1
                steps = 0
                limit_steps = random.randint(min_steps, max_steps)

                while steps < limit_steps and curr_state in states:
                    st_data = states[curr_state]
                    ts = int(time.time()) + (line_id * 10)
                    st_type = str(st_data.get('type', ''))
                    
                    # --- LÓGICA DE ACTOR (BASADA EN SEMÁNTICA DEL JSON) ---
                    cat = str(st_data.get('category', '')).upper()
                    codes_text = ""
                    for c in st_data.get("codes", []): codes_text += f" {c.get('display', '').upper()}"
                    target = f"{curr_state} {st_type} {cat} {codes_text}".upper()

                    if st_type == "Death" or "DEATH" in target:
                        actor = "Medical_Examiner"
                    elif any(x in target for x in ["CANCER", "ONCOLOGY", "TUMOR", "MAMMOGRAM"]):
                        actor = "Oncologist"
                    elif cat == "LABORATORY" or any(x in target for x in ["BLOOD", "URINE", "PANEL", "LOINC", "TEST"]):
                        actor = "Lab_Technician"
                    elif any(x in target for x in ["IMAGING", "XRAY", "SCAN", "MRI", "ULTRASOUND"]):
                        actor = "Radiologist"
                    elif any(x in target for x in ["MEDICATION", "PRESCRIPTION", "RX", "DRUG", "IMMUNIZATION"]):
                        actor = "Pharmacist"
                    elif any(x in target for x in ["SURGERY", "BIOPSY", "EXCISION", "APPENDY"]):
                        actor = "Surgeon"
                    elif any(x in target for x in ["EMERGENCY", "TRIAGE", "ED_VISIT"]):
                        actor = "ER_Staff"
                    elif "CAREPLAN" in st_type:
                        actor = "Care_Manager"
                    elif st_data.get('wellness', False):
                        actor = "Primary_Care_Physician"
                    elif any(x in target for x in ["CONDITION", "DIAGNOSIS", "SYMPTOM"]):
                        actor = "Physician"
                    elif st_type in ["Initial", "Terminal", "Delay", "SetAttribute"]:
                        actor = "Clinical_System"
                    else:
                        actor = "Practitioner"

                    # SNOMED
                    first_sn = "0"
                    for c in st_data.get("codes", []):
                        if "SNOMED" in c.get("system", "").upper():
                            first_sn = c["code"]; break

                    # Guardar línea MOD (CSV format)
                    proc_uri = f"<http://example.org/procedure/{wf_name}/{clean(curr_state)}>"
                    mod_lines.append(f"{curr_state},{ts},{actor},at_{st_type},{proc_uri},{snomed_uri(first_sn)},{wf_name}")

                    # --- TRANSICIÓN SEGURA (CORRECCIÓN DEL KEYERROR) ---
                    next_s = None
                    if "direct_transition" in st_data:
                        next_s = st_data["direct_transition"]
                    elif "conditional_transition" in st_data:
                        next_s = random.choice(st_data["conditional_transition"])["transition"]
                    elif "distributed_transition" in st_data:
                        next_s = random.choice(st_data["distributed_transition"])["transition"]
                    elif "complex_transition" in st_data:
                        # Buscamos 'distributions' de forma segura en la estructura compleja
                        try:
                            item = st_data["complex_transition"][0]
                            if "distributions" in item:
                                next_s = random.choice(item["distributions"])["transition"]
                            elif "transition" in item:
                                next_s = item["transition"]
                        except (IndexError, KeyError): pass

                    if not next_s or next_s not in states: break
                    curr_state = next_s
                    line_id += 1
                    steps += 1

        with open(output_mod, "w", encoding="utf-8") as f:
            f.write("\n".join(mod_lines))

print(f"✔ Finalizado: {output_mod}")
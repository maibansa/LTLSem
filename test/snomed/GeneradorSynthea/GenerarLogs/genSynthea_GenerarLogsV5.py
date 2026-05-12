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
#Número de trazas por workflow (total será este número multiplicado por la cantidad de workflows)
LISTA_NUM_TRACES = (5, 10, 50, 100, 500, 1000, 5000, 10000)
RANGOS_PASOS = ((6, 20), (21, 40), (41, 60), (61, 80))

LISTA_NUM_TRACES = (100,)
RANGOS_PASOS = ((61, 80),)

# -----------------------------
# HELPERS SEMÁNTICOS
# -----------------------------
def snomed_uri(code): return f"<http://snomed.info/id/{code}>"
def clean(txt): return str(txt).replace(" ", "_").replace('"', "").replace("'", "").replace("\n", " ")

def extract_all_codes_recursive(data):
    """
    Busca de forma exhaustiva cualquier diccionario que contenga 'code' y 'system'
    dentro de cualquier estructura (listas, diccionarios anidados, etc.)
    """
    found = []
    if isinstance(data, dict):
        # Si detectamos la estructura de un código clínico
        if "code" in data and "system" in data:
            found.append(data)
        # Seguimos buscando en todas las llaves del diccionario
        for value in data.values():
            found.extend(extract_all_codes_recursive(value))
    elif isinstance(data, list):
        # Si es una lista, buscamos en cada elemento
        for item in data:
            found.extend(extract_all_codes_recursive(item))
    return found

def get_deep_semantics(state_name, st_data, event_uri, wf_name):
    q = []
    proc_uri = f"<http://example.org/procedure/{wf_name}/{clean(state_name)}>"
    
    # 1. Metadatos básicos y Tipo de Estado
    q.append(f"{proc_uri} <http://www.w3.org/2000/01/rdf-schema#label> \"{clean(state_name)}\" {event_uri} .")
    st_type = st_data.get("type", "State")
    q.append(f"{proc_uri} <http://example.org/ontology/hasStateType> \"{st_type}\" {event_uri} .")

    # 2. Captura de Categoría (Crucial para "Pain_Vital")
    if "category" in st_data:
        cat = clean(st_data["category"])
        q.append(f"{proc_uri} <http://example.org/ontology/hasCategory> \"{cat}\" {event_uri} .")

    # 3. Captura de Remarks (Contexto clínico que no es código)
    # En Fibromialgia, los remarks explican el uso de Lyrica/Opioides
    remarks = st_data.get("remarks", [])
    if isinstance(remarks, list):
        full_remark = " ".join(remarks)
        if full_remark.strip():
            q.append(f"{proc_uri} <http://example.org/ontology/clinicalRemark> \"{clean(full_remark)}\" {event_uri} .")

    # --- RECOLECTOR RECURSIVO DE CÓDIGOS (SNOMED, RxNorm, LOINC) ---
    all_raw_codes = extract_all_codes_recursive(st_data)
    processed_uris = set()

    for c in all_raw_codes:
        if not c or not isinstance(c, dict): continue
        sys = clean(c.get("system", "unknown"))
        code = clean(c.get("code", "0"))
        label = clean(c.get("display", "N/A"))
        
        # Mapeo de URIs estándar
        if "SNOMED" in sys.upper(): c_uri = f"<http://snomed.info/id/{code}>"
        elif "LOINC" in sys.upper(): c_uri = f"<http://loinc.org/rdf/{code}>"
        elif "RXNORM" in sys.upper(): c_uri = f"<http://rxnav.nlm.nih.gov/REST/rxcui/{code}>"
        else: c_uri = f"<http://example.org/code/{sys}/{code}>"

        if c_uri not in processed_uris:
            q.append(f"{proc_uri} <http://example.org/ontology/clinicalCode> {c_uri} {event_uri} .")
            q.append(f"{c_uri} <http://www.w3.org/2000/01/rdf-schema#label> \"{label}\" {event_uri} .")
            processed_uris.add(c_uri)

    # 4. Captura de Atributos y su importancia (assign_to_attribute)
    # En Fibromialgia esto captura "fibromyalgia_prescription" u "opioid_prescription"
    attr_key = st_data.get("assign_to_attribute") or st_data.get("attribute")
    if attr_key:
        q.append(f"{proc_uri} <http://example.org/ontology/managesAttribute> \"{clean(attr_key)}\" {event_uri} .")

    # 5. Captura de Rangos de Observación / Síntomas
    # Para Pain_Vital (rango 5-10) y Síntomas (rango 25-100)
    if "range" in st_data:
        r = st_data["range"]
        low, high = r.get("low", "0"), r.get("high", "0")
        unit = st_data.get("unit", "score")
        q.append(f"{proc_uri} <http://example.org/ontology/hasRange> \"{low}-{high}\" {event_uri} .")
        q.append(f"{proc_uri} <http://example.org/ontology/hasUnit> \"{clean(unit)}\" {event_uri} .")

    # 6. Referencias a estados previos (MedicationEnd/CarePlanEnd)
    ref_fields = ["careplan", "medication_order", "referenced_by_attribute"]
    for field in ref_fields:
        if field in st_data:
            q.append(f"{proc_uri} <http://example.org/ontology/referencesVariable> \"{clean(st_data[field])}\" {event_uri} .")

    return q
# -----------------------------
# EJECUCIÓN POR EXPERIMENTO
# -----------------------------

for num_traces in LISTA_NUM_TRACES:
    for min_steps, max_steps in RANGOS_PASOS:
        
        # Nombre de archivo solicitado: log_NUM_TRACES_MIN_STEPS_MAX_STEPS
        base_filename = f"log_{num_traces*len(WORKFLOWS)}_{min_steps}_{max_steps}"
        output_mod = os.path.join(AUTO_DIR, f"{base_filename}.mod")
        output_nq = os.path.join(AUTO_DIR, f"{base_filename}.nq")
        
        mod_lines = ["aActivity,nTimestamp,sActor,aActionType,sModelReference,sSnomed,aWorkflow"]
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

                    # --- NUEVA LÓGICA PARA EL ACTOR ---
                    # Intentamos sacar el actor de 'operator' o 'assigned_to', 
                    # si no, usamos 'Provider' como estándar de Synthea
                    raw_actor = st_data.get("operator", "Provider")
                    actor = clean(raw_actor)

                    # --- GENERAR MOD ---
                    f# --- EXTRAER SNOMED PARA EL .MOD (Lógica mejorada) ---
                    # --- BUSCAR EL SNOMED PARA EL .MOD ---
# --- BUSCAR EL SNOMED PARA EL .MOD ---
                    first_snomed = "0"
                    # Prioridad: codes > value_code > activities > discharge
                    search_list = st_data.get("codes", [])[:]
                    if "value_code" in st_data: search_list.append(st_data["value_code"])
                    if "discharge_disposition" in st_data: search_list.append(st_data["discharge_disposition"])
                    for act in st_data.get("activities", []): 
                        search_list.extend(act.get("codes", []))

                    # Buscamos el primer código que sea SNOMED
                    for c in search_list:
                        if c and isinstance(c, dict) and "SNOMED" in str(c.get("system", "")).upper():
                            first_snomed = str(c.get("code", "0"))
                            break                    

                    
                # --- LÓGICA DE ACTOR BASADA 100% EN PALABRAS CLAVE DEL JSON ---
                    st_type_raw = str(st_data.get('type', ''))
                    st_name_raw = str(curr_state)
                    
                    # Extraemos campos adicionales que aparecen en tus archivos como 'category' o 'wellness'
                    st_category = str(st_data.get('category', '')).upper()
                    is_wellness = st_data.get('wellness', False)

                    # Concatenamos todo para la búsqueda
                    search_target = f"{st_type_raw} {st_name_raw} {st_category}".upper()
                    
                   # --- LÓGICA DE ACTOR MEJORADA ---
                    st_type_raw = str(st_data.get('type', '')).upper()
                    st_name_raw = str(curr_state).upper()
                    st_category = str(st_data.get('category', '')).upper()
                    is_wellness = st_data.get('wellness', False)

                    # Concatenamos todo para la búsqueda de palabras clave
                    search_target = f"{st_type_raw} {st_name_raw} {st_category}".upper()

                  # 1. Reglas basadas en la estructura real de tus archivos JSON
                    if is_wellness or "WELLNESS" in search_target:
                        actor = "Primary_Care_Physician"

                    # PRIORIDAD: Si es una emergencia (como en la Epilepsia), que mande el ER_Staff
                    elif any(x in search_target for x in ["EMERGENCY", "ED_VISIT", "TRIAGE"]):
                        actor = "ER_Staff"

                    # CONSULTAS Y SUBMÓDULOS: Practicante general
                    elif any(x in search_target for x in ["ENCOUNTER", "CONSULTATION", "VISIT", "SUBMODULE"]):
                        actor = "Practitioner"

                    # DIAGNÓSTICOS Y SÍNTOMAS: Aquí es donde cae la mayoría del Asma
                    elif any(x in search_target for x in ["CONDITION", "SYMPTOM", "DIAGNOSIS", "ONSET"]):
                        actor = "Physician"

                    # MEDICAMENTOS: Farmacéutico
                    elif any(x in search_target for x in ["MEDICATION", "PRESCRIPTION", "DRUG", "RX", "IMMUNIZATION"]):
                        actor = "Pharmacist"

                    # PRUEBAS Y LABORATORIO (EEG en Epilepsia, por ejemplo): Técnico de laboratorio
                    elif any(x in search_target for x in ["OBSERVATION", "LAB", "VITAL", "BLOOD", "URINE", "PANEL", "TEST", "EEG"]):
                        actor = "Lab_Technician"

                    # CIRUGÍAS
                    elif any(x in search_target for x in ["PROCEDURE", "SURGERY", "BIOPSY", "EXCISION"]):
                        actor = "Surgeon"

                    # RADIOLOGÍA E IMAGEN
                    elif any(x in search_target for x in ["IMAGING", "XRAY", "SCAN", "MRI", "CT", "MAMMOGRAM", "ULTRASOUND"]):
                        actor = "Radiologist"

                    # PLANES DE CUIDADO (El Asma tiene varios CarePlan)
                    elif any(x in search_target for x in ["CAREPLAN", "PLAN"]):
                        actor = "Care_Manager"

                    # MUERTE
                    elif "DEATH" in search_target:
                        actor = "Medical_Examiner"

                    else:
                        # Actor por defecto si no detecta nada médico
                        actor = "Clinical_System"
                   # --- BUSCAR EL PRIMER SNOMED EN CUALQUIER LUGAR ---
                    first_snomed = "0"
                    # Lista de prioridad: códigos normales -> valores -> actividades
                   # --- 1. PREPARAR LA LISTA DE BÚSQUEDA ---
                    search_list = st_data.get("codes", [])[:]
                    if "value_code" in st_data: search_list.append(st_data["value_code"])
                    if "discharge_disposition" in st_data: search_list.append(st_data["discharge_disposition"])
                    for act in st_data.get("activities", []): 
                        search_list.extend(act.get("codes", []))

                    # --- 2. BUSCAR EL CÓDIGO ---
                    first_snomed = "0"
                    for c in search_list:
                        if c and isinstance(c, dict) and "SNOMED" in str(c.get("system", "")).upper():
                            first_snomed = c["code"]
                            break

                    # --- LÍNEA 121 CORREGIDA ---
                    mod_lines.append(f"{trace_id},{curr_state}&{ts}&{actor}&at_{st_type_raw}&{snomed_uri(first_snomed)}&{event_uri}&{wf_name}")
                    nq_lines.append(f"{case_uri} <http://example.org/ontology/hasEvent> {event_uri} {event_uri} .")
                    nq_lines.append(f"{event_uri} <http://example.org/ontology/executes> {proc_uri} {event_uri} .")
                    nq_lines.extend(get_deep_semantics(curr_state, st_data, event_uri, wf_name))
                    
                    if line_id > 1:
                        prev_event = f"<http://example.org/event/{trace_id}_L{line_id-1}>"
                        nq_lines.append(f"{event_uri} <http://example.org/ontology/follows> {prev_event} {event_uri} .")

                    # --- TRANSICIÓN ---
                    # --- TRANSICIÓN (CORREGIDA PARA QUE NO SE DETENGA) ---
                    # --- LÓGICA DE TRANSICIÓN "ANTI-ERRORES" ---
                    next_s = None
                    
                    # --- TRANSICIÓN ROBUSTA (PARA ASMA Y EPILEPSIA) ---
                    next_s = None
                    
                    if "direct_transition" in st_data:
                        next_s = st_data["direct_transition"]

                    elif "distributed_transition" in st_data:
                        dist = st_data["distributed_transition"]
                        next_s = random.choices(
                            [d["transition"] for d in dist], 
                            weights=[d.get("distribution", 0) for d in dist]
                        )[0]

                    elif "complex_transition" in st_data:
                        for entry in st_data["complex_transition"]:
                            if "distributions" in entry:
                                dist = entry["distributions"]
                                next_s = random.choices([d["transition"] for d in dist], weights=[d.get("distribution", 0) for d in dist])[0]
                                break
                            elif "transition" in entry:
                                next_s = entry["transition"]
                                break

                    elif "conditional_transition" in st_data:
                        # Asma tiene condiciones de Atopia/Fumador/Edad. 
                        # Seleccionamos una al azar para que la traza siga viva.
                        next_s = random.choice(st_data["conditional_transition"])["transition"]

                    # --- PARCHE PARA SUBMÓDULOS (ASMA) ---
                    if st_data.get("type") == "CallSubmodule" and not next_s:
                        # Si no hay transición definida pero es un CallSubmodule, 
                        # intentamos seguir adelante (o terminar si no hay nada)
                        next_s = "Terminal" 

                    # --- CIERRE DE TRAZA ---
                    if not next_s or next_s == "Terminal" or next_s not in states:
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
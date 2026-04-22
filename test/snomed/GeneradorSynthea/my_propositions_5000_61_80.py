import sys
from pyoxigraph import Store
import time
# Configuración: La ruta a tu carpeta de base de datos
path_auto = "./test/snomed/GeneradorSynthea/auto"
DB_PATH = f"{path_auto}/log_5000_61_80"

# Inicializamos el store una sola vez para todas las consultas
store = Store(DB_PATH, read_only=True)

def ask_query(q):
    t0 = time.perf_counter()
    result = bool(store.query(q))
    t1 = time.perf_counter()
   # print(f"  ask_query: {t1-t0:.4f}s -> {result}")
    return result


def IsDiagnosis(g1):
    q = f"""
    PREFIX snomed: <http://snomed.info/snomed#>
    PREFIX sct: <http://snomed.info/id/>

    ASK WHERE {{
        GRAPH {g1} {{
            ?s <http://example.org/ontology/hasStateType> "Encounter"
        }}
    }}"""
    return ask_query(q)


def IsMedication(g1):
    q = f"""
    PREFIX ont: <http://example.org/ontology/>
    ASK WHERE {{
        GRAPH {g1} {{
            ?s ont:hasStateType "MedicationOrder" .
        }}
    }}"""
    return ask_query(q)


def IsCarePlanActivity(g1):
    q = f"""
    PREFIX ont: <http://example.org/ontology/>
    ASK WHERE {{
        GRAPH {g1} {{
            ?s ont:hasStateType "CarePlanStart" .
        }}
    }}"""
    return ask_query(q)


def IsProcedure(g1):
    q = f"""
    PREFIX ont: <http://example.org/ontology/>
    ASK WHERE {{
        GRAPH {g1} {{
            ?s ont:hasStateType "Procedure" .
        }}
    }}"""
    return ask_query(q)


def HasSnomedCode(g1, code):
    q = f"""
    PREFIX ont: <http://example.org/ontology/>
    ASK WHERE {{
        GRAPH {g1} {{
            ?event ont:executes ?proc .
            ?proc ont:clinicalCode <http://snomed.info/id/{code}> .
        }}
    }}"""
    return ask_query(q)


def RequiresAttribute(g1, attr_name):
    q = f"""
    PREFIX ont: <http://example.org/ontology/>
    ASK WHERE {{
        GRAPH {g1} {{
            ?event ont:executes ?proc .
            ?proc ont:monitorsAttribute "{attr_name}" .
        }}
    }}"""
    return ask_query(q)


def AuditTrail(g1, g2):
    q = f"""
    PREFIX ont: <http://example.org/ontology/>
    ASK WHERE {{
        GRAPH {g2} {{
            {g2} ont:follows {g1} .
        }}
    }}"""
    return ask_query(q)


def SameSnomedCode(g1, g2):
    q = f"""
    PREFIX ont: <http://example.org/ontology/>
    ASK WHERE {{
        GRAPH {g1} {{
            ?event1 ont:executes ?proc1 .
            ?proc1 ont:clinicalCode ?snomedCode .
        }}
        GRAPH {g2} {{
            ?event2 ont:executes ?proc2 .
            ?proc2 ont:clinicalCode ?snomedCode .
            FILTER(CONTAINS(STR(?snomedCode), "snomed.info"))
        }}
    }}"""
    return ask_query(q)


def IsSnomedFollowup(g1, g2):
    q = f"""
    PREFIX ont: <http://example.org/ontology/>
    ASK WHERE {{
        GRAPH {g1} {{
            ?e1 ont:executes ?p1 .
            ?p1 ont:clinicalCode ?c1 .
        }}
        GRAPH {g2} {{
            {g2} ont:follows {g1} .
            ?e2 ont:executes ?p2 .
            ?p2 ont:clinicalCode ?c2 .
            FILTER(CONTAINS(STR(?c1), "snomed.info") && CONTAINS(STR(?c2), "snomed.info"))
        }}
    }}"""
    return ask_query(q)


def DiagnosisMatchesTreatment(g1, g2):
    q = f"""
    PREFIX ont: <http://example.org/ontology/>
    ASK WHERE {{
        GRAPH {g1} {{
            ?e1 ont:hasStateType "Encounter" .
            ?e1 ont:executes ?p1 .
            ?p1 ont:clinicalCode ?diagCode .
        }}
        GRAPH {g2} {{
            ?e2 ont:hasStateType "MedicationOrder" .
            ?e2 ont:executes ?p2 .
            ?p2 ont:clinicalCode ?treatCode .
            FILTER(CONTAINS(STR(?diagCode), "snomed.info"))
        }}
    }}"""
    return ask_query(q)


def FollowsWithDiagnosis(g1, g2):
    q = f"""
    PREFIX ont: <http://example.org/ontology/>
    ASK WHERE {{
        GRAPH {g2} {{
            {g2} ont:follows {g1} .
            ?event ont:hasStateType "Encounter" .
        }}
    }}"""
    return ask_query(q)


def SnomedChain3(g1, g2, g3):
    q = f"""
    PREFIX ont: <http://example.org/ontology/>
    ASK WHERE {{
        GRAPH {g1} {{
            ?e1 ont:executes ?p1 .
            ?p1 ont:clinicalCode ?snomed .
        }}
        GRAPH {g2} {{
            {g2} ont:follows {g1} .
            ?e2 ont:executes ?p2 .
            ?p2 ont:clinicalCode ?snomed .
        }}
        GRAPH {g3} {{
            {g3} ont:follows {g2} .
            ?e3 ont:executes ?p3 .
            ?p3 ont:clinicalCode ?snomed .
        }}
        FILTER(CONTAINS(STR(?snomed), "snomed.info"))
    }}"""
    return ask_query(q)


def DiagnosisTreatmentSnomed(g1, g2, g3):
    q = f"""
    PREFIX ont: <http://example.org/ontology/>
    ASK WHERE {{
        GRAPH {g1} {{
            ?e1 ont:hasStateType "Encounter" .
            ?e1 ont:executes ?p1 .
            ?p1 ont:clinicalCode ?code1 .
        }}
        GRAPH {g2} {{
            {g2} ont:follows {g1} .
            ?e2 ont:hasStateType "MedicationOrder" .
        }}
        GRAPH {g3} {{
            {g3} ont:follows {g2} .
            ?e3 ont:executes ?p3 .
            ?p3 ont:clinicalCode ?code1 .
        }}
        FILTER(CONTAINS(STR(?code1), "snomed.info"))
    }}"""
    return ask_query(q)


def SnomedEvolution(g1, g2, g3):
    q = f"""
    PREFIX ont: <http://example.org/ontology/>
    ASK WHERE {{
        GRAPH {g1} {{
            ?e1 ont:executes ?p1 .
            ?p1 ont:clinicalCode ?c1 .
        }}
        GRAPH {g2} {{
            {g2} ont:follows {g1} .
        }}
        GRAPH {g3} {{
            {g3} ont:follows {g2} .
            ?e3 ont:executes ?p3 .
            ?p3 ont:clinicalCode ?c3 .
        }}
        FILTER(CONTAINS(STR(?c1), "snomed.info") && CONTAINS(STR(?c3), "snomed.info"))
    }}"""
    return ask_query(q)


def MultiSnomedValidation(g1, g2, g3):
    q = f"""
    PREFIX ont: <http://example.org/ontology/>
    ASK WHERE {{
        GRAPH {g1} {{ ?e1 ont:executes ?p1 . ?p1 ont:clinicalCode ?c1 . }}
        GRAPH {g2} {{
            {g2} ont:follows {g1} .
            ?e2 ont:executes ?p2 . ?p2 ont:clinicalCode ?c2 .
        }}
        GRAPH {g3} {{ {g3} ont:follows {g2} . }}
        FILTER(CONTAINS(STR(?c1), "snomed.info") && CONTAINS(STR(?c2), "snomed.info") && ?c1 != ?c2)
    }}"""
    return ask_query(q)
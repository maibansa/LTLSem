from rdflib import Dataset
file_path = f"test/snomed/GeneradorSynthea/auto/log_50_6_20.nq"
g = Dataset()
g.parse(source=file_path, format="nquads")



def IsDiagnosis(g1):
     
    q = f"""
    PREFIX snomed: <http://snomed.info/snomed#>
    PREFIX sct: <http://snomed.info/id/>
    
    ASK WHERE {{
        GRAPH {g1} {{
          ?s  <http://example.org/ontology/hasStateType> "Encounter"
           
        }}
    }}"""
    
    return g.query(q).askAnswer

def IsMedication(g1):
    q = f"""
    PREFIX ont: <http://example.org/ontology/>
    ASK WHERE {{
        GRAPH {g1} {{
            ?s ont:hasStateType "MedicationOrder" .
        }}
    }}"""
    return g.query(q).askAnswer

def IsCarePlanActivity(g1):
    q = f"""
    PREFIX ont: <http://example.org/ontology/>
    ASK WHERE {{
        GRAPH {g1} {{
            ?s ont:hasStateType "CarePlanStart" .
        }}
    }}"""
    return g.query(q).askAnswer

def IsProcedure(g1):
    q = f"""
    PREFIX ont: <http://example.org/ontology/>
    ASK WHERE {{
        GRAPH {g1} {{
            ?s ont:hasStateType "Procedure" .
        }}
    }}"""
    return g.query(q).askAnswer

def HasSnomedCode(g1, code):
    q = f"""
    PREFIX ont: <http://example.org/ontology/>
    ASK WHERE {{
        GRAPH {g1} {{
            ?event ont:executes ?proc .
            ?proc ont:clinicalCode <http://snomed.info/id/{code}> .
        }}
    }}"""
    return g.query(q).askAnswer

def RequiresAttribute(g1, attr_name):
    q = f"""
    PREFIX ont: <http://example.org/ontology/>
    ASK WHERE {{
        GRAPH {g1} {{
            ?event ont:executes ?proc .
            ?proc ont:monitorsAttribute "{attr_name}" .
        }}
    }}"""
    return g.query(q).askAnswer

def AuditTrail(g1, g2):
    # Usando el predicado 'follows' que unifica los grafos en tu .nq
    q = f"""
    PREFIX ont: <http://example.org/ontology/>
    ASK WHERE {{
        GRAPH {g2} {{ 
            {g2} ont:follows {g1} .
        }}
    }}"""
    return g.query(q).askAnswer


def SameSnomedCode(g1, g2):
    """
    Verifica si el evento x y el evento y tienen exactamente 
    el mismo código clínico de SNOMED.
    """
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
    return g.query(q).askAnswer

def IsSnomedFollowup(g1, g2):
    """
    Verifica si g2 es un evento de SNOMED que sigue a un 
    evento g1 (que también tiene código SNOMED).
    """
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
    return g.query(q).askAnswer

def DiagnosisMatchesTreatment(g1, g2):
    """
    Relaciona un diagnóstico en g1 con un tratamiento en g2 
    siempre que ambos tengan códigos SNOMED vinculados.
    """
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
    return g.query(q).askAnswer

def FollowsWithDiagnosis(g1, g2):
    """
    Verifica que g2 sigue a g1 y que g2 es un diagnóstico (Encounter).
    """
    q = f"""
    PREFIX ont: <http://example.org/ontology/>
    ASK WHERE {{
        GRAPH {g2} {{ 
            {g2} ont:follows {g1} .
            ?event ont:hasStateType "Encounter" .
        }}
    }}"""
    return g.query(q).askAnswer

def SnomedChain3(g1, g2, g3):
    """
    Verifica si existe una secuencia de tres eventos (g1 -> g2 -> g3)
    donde los tres comparten exactamente el mismo código SNOMED.
    Útil para rastrear el seguimiento de una misma patología.
    """
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
    return g.query(q).askAnswer


def DiagnosisTreatmentSnomed(g1, g2, g3):
    """
    Valida una secuencia donde:
    g1: Es un encuentro inicial (Encounter) con código SNOMED.
    g2: Es una orden de medicación (MedicationOrder) que sigue a g1.
    g3: Es un seguimiento con un código SNOMED que coincide con el original de g1.
    """
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
    return g.query(q).askAnswer


def SnomedEvolution(g1, g2, g3):
    """
    Verifica una secuencia de tres eventos donde g1 y g3 tienen códigos SNOMED,
    pero g2 es un evento intermedio (como un Delay o espera) sin necesidad de código.
    """
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
    return g.query(q).askAnswer


def MultiSnomedValidation(g1, g2, g3):
    """
    Verifica si g3 sigue a g2 y g2 sigue a g1, y asegura que 
    al menos dos de estos eventos tengan códigos SNOMED distintos 
    (indicando cambio de fase o complicación).
    """
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
    return g.query(q).askAnswer
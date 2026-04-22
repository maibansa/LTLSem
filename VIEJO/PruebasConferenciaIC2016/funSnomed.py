
# python MC.py log-file=test/snomed/WFSemTrazas2V2
# _LOAD PROP H:\\Hpy_MC-main_working\\py_MC-main_working\\test\\snomed\\funSnomed.py  


from rdflib import Dataset
file_path = "test/snomed/Snomedlog2.nq"
g = Dataset()
print(f"Cargando datos desde '{file_path}'...")
g.parse(source=file_path, format="nquads")
print("Datos cargados exitosamente.")


# ===============================================
#Consistencia Triage-Acción (Seguridad Crítica)
# Verifica si un hallazgo de alta severidad (G1/Line_1) disparó la creación 
# de un plan de emergencia específico (G2/Line_2).
# Esta query actúa como un "puente" de seguridad clínica que conecta dos momentos 
# clave del historial del paciente para garantizar que no existan omisiones en su 
# cuidado. En el primer bloque (Grafo 1), la consulta identifica una situación de 
# riesgo crítico —un triage de alta severidad— y captura la identidad del paciente 
# (?caso) y el evento específico (?triage). Inmediatamente, el motor de búsqueda 
# utiliza esa información como ancla para inspeccionar el segundo bloque (Grafo 2), 
# donde exige encontrar un plan de acción que no solo pertenezca al mismo individuo,
#  sino que declare explícitamente ser una respuesta directa (inResponseTo) a la alerta
#  previa. Al basarse en la identidad de los recursos (IRIs) y no en cálculos numéricos
#  o formatos de fecha, la query asegura un resultado robusto y binario: confirma si la
#  cadena de mando clínica se cumplió o si se rompió la continuidad asistencial ante 
# una urgencia.
# LIGADO: La variable ?caso unifica al paciente entre el hallazgo y la respuesta.
# ?triage vincula el procedimiento de evaluación con la notificación posterior.
# DLTL -> F x.(X F y.("(x,y)PROP.TriageResponseConsistency(x[Snomed],y[Snomed])")) 
# 3,27,10.0,26.81
# DLTL -> _WHO
# Case_HighSeverity_1 Case_HighSeverity_2 Case_HighSeverity_3 
# DLTL -> F x.(X F y.("(x,y)y[Timestamp] - x[Timestamp] >= 43200" & "(x,y)PROP.TriageResponseConsistency(x[Snomed],y[Snomed])")) 
# 1,29,3.33,16.8
# DLTL -> _WHO
# Case_HighSeverity_3 


# ===============================================
def TriageResponseConsistency(g1, g2):
    q = f"""PREFIX snomed: <http://snomed.info/snomed#>
    ASK WHERE {{
        # En Grafo 1 (Line_1): Buscamos el nivel de triage alto
        GRAPH {g1} {{ 
            ?caso snomed:undergoes ?triage .
            ?triage snomed:triageLevel "High_severity" .
        }}
        # En Grafo 2 (Line_2): Verificamos que se creó un plan de respuesta
        GRAPH {g2} {{ 
            ?caso snomed:hasPlan ?plan .
            ?plan snomed:appointmentType "Telehealth_consultation" ;
                  snomed:inResponseTo ?triage .
        }}
    }}"""
    return g.query(q).askAnswer

# ===============================================
# Auditoría de Preparación: "Shadowing" del Médico
# Verifica si el médico accedió a los registros históricos (G1) 
# que luego revisó durante la consulta real (G2).
# LIGADO: Cruza la acción de acceso y el procedimiento clínico mediante ?caso.
# F x.(X F y.("(x,y)PROP.AuditTrail(x[Snomed],y[Snomed])")) 
# DLTL -> F x.(X F y.("(x,y)PROP.AuditTrail(x[Snomed],y[Snomed])"))
# 1,29,3.33,30.18
# DLTL -> _WHO
# Case_HighSeverity_1 
# ===============================================
def AuditTrail(g1, g2):
    q = f"""PREFIX snomed: <http://snomed.info/snomed#>
    PREFIX sct: <http://snomed.info/id/>
    ASK WHERE {{
        GRAPH {g1} {{ 
            ?caso snomed:hasPlan ?plan . 
            ?plan snomed:hasComponent ?acc . 
            ?acc a sct:386414003 ; snomed:accesses <http://example.org/record/current_meds_001> . 
        }}
        GRAPH {g2} {{ 
            ?caso snomed:undergoes ?proc . 
            ?proc snomed:hasComponent ?rev . 
            ?rev a sct:410684002 . # medication review procedure [cite: 30]
        }}
    }}"""
    return g.query(q).askAnswer




# ===============================================
# Coherencia de los "Componentes" del Plan
# Verifica que si se recetó un antibiótico en el plan (G1), 
# exista un diagnóstico compatible en la evaluación (G2).
# LIGADO: Asegura la consistencia terapéutica dentro del mismo ?caso.
# F x.(X F y.("(x,y)PROP.AuditTrail(x[Snomed],y[Snomed])")) 
# DLTL -> F x.(X F y.("(x,y)PROP.AuditTrail(x[Snomed],y[Snomed])")) 
# 1,29,3.33,34.03
# DLTL -> _WHO
# Case_HighSeverity_1
# ===============================================
def PlanComponentCoherence(g1, g2):
    q = f"""PREFIX snomed: <http://snomed.info/snomed#>
    ASK WHERE {{
        GRAPH {g1} {{
            ?caso snomed:hasPlan ?plan .
            ?plan snomed:includesMedication "Amoxicillin" .
        }}
        GRAPH {g2} {{
            ?caso snomed:undergoes ?proc .
            ?proc snomed:assesses "Bacterial_infection" .
        }}
    }}"""
    return g.query(q).askAnswer



# ===============================================
# La función run_feedback_loop_check valida que se complete correctamente un ciclo de retroalimentación clínica en tres puntos clave. Primero verifica que el paciente se encontraba en estado pendiente de acción en la línea inicial del proceso. Segundo, confirma que el paciente efectivamente fue sometido a una revisión de expertos durante el seguimiento. Finalmente, comprueba que el protocolo o plan de acción fue actualizado como resultado del feedback recibido en la revisión clínica.
# F x.(X F y.(X F z.("(x,y,z)PROP.run_feedback_loop_check(x[Snomed],y[Snomed],z[Snomed])")))
#DLTL -> F x.(X F y.(X F z.("(x,y,z)PROP.run_feedback_loop_check(x[Snomed],y[Snomed],z[Snomed])")))
#_WHO
# 30,0,100.0,369.25
#DLTL -> _WHO
#Case_HighSeverity_1 Case_HighSeverity_10 Case_HighSeverity_2 Case_HighSeverity_3 Case_HighSeverity_4 Case_HighSeverity_5 Case_HighSeverity_6 Case_HighSeverity_7 Case_HighSeverity_8 Case_HighSeverity_9 Case_LowSeverity_1 Case_LowSeverity_10 Case_LowSeverity_2 Case_LowSeverity_3 Case_LowSeverity_4 Case_LowSeverity_5 Case_LowSeverity_6 Case_LowSeverity_7 Case_LowSeverity_8 Case_LowSeverity_9 Case_MedSeverity_1 Case_MedSeverity_10 Case_MedSeverity_2 Case_MedSeverity_3 Case_MedSeverity_4 Case_MedSeverity_5 Case_MedSeverity_6 Case_MedSeverity_7 Case_MedSeverity_8 Case_MedSeverity_9
def run_feedback_loop_check(g1,g2,g3):
   
    q = f"""
    PREFIX snomed: <http://snomed.info/snomed#>
    
    ASK WHERE {{
        # 1. ¿Estaba el paciente en estado pendiente en la entrada (L2)?
        GRAPH {g1} {{ 
            ?patient snomed:hasStatus "Pending_Action" . 
        }}
        
        # 2. ¿Pasó realmente por la revisión de expertos (L3)?
        GRAPH {g2} {{ 
            ?patient snomed:undergoes "Clinical_Review_Process" . 
        }}
        
        # 3. ¿Se actualizó el protocolo en la salida (L8)?
        GRAPH {g3} {{ 
            ?patient snomed:hasStatus "Action_Adjusted_by_Feedback" . 
        }}
    }}"""
    
    return g.query(q).askAnswer






    # Si se le ha recetado un antibiótico, pero nunca ha tenido una infección bacteriana anteriormente
    # Se ha recetado un antibiótico, pero no tenia que haberlo hecho.
    #  F x.("(x)PROP.ANT(x[Snomed])" & H y.(!"(y)PROP.BACT(y[Snomed])"))
    # ANT# Función and que le pasas un estado y te dice true si es receta de antibiotico. 
    # BACTOtra función que me dice si hay infección bacteriana. .
    # DLTL -> F x.("(x)PROP.ANT(x[Snomed])" & H y.(!"(y)PROP.BACT(y[Snomed])"))
    # 1,29,3.33,8.23
    # DLTL -> _WHO
    # Case_HighSeverity_1 
    ## DLTL -> F x.("(x)PROP.ANT2(x[Snomed])" & H y.(!"(y)PROP.BACT(y[Snomed])"))


def ANT(g1):
  
    q = f"""PREFIX snomed: <http://snomed.info/snomed#>\n\n
    ASK WHERE {{\n    
    GRAPH {g1}
      {{ \n       ?caso snomed:hasPlan ?plan .
            ?plan snomed:includesMedication "Amoxicillin" . \n    }}\n}}"""
   
    return g.query(q).askAnswer

def ANT2(g1):
    q = f"""PREFIX snomed: <http://snomed.info/snomed#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

    ASK WHERE {{
        GRAPH <http://example.org/Line_0>  {{
            ?antibiotico rdfs:subClassOf snomed:373270004 .
        }}
        GRAPH {g1} {{
            ?caso snomed:hasPlan ?plan .
            ?plan snomed:includesMedication ?antibiotico .
        }}
    }}"""
    return g.query(q).askAnswer

def BACT(g1):
  
    q = f"""PREFIX snomed: <http://snomed.info/snomed#>\n\n
    ASK WHERE {{\n    
    GRAPH {g1}
      {{ \n       ?caso snomed:undergoes ?proc .
            ?proc snomed:assesses "Bacterial_infection" . \n    }}\n}}"""
   
    return g.query(q).askAnswer


# Si en algún momento hay un "resultado disponible" es porque alquien lo ha prescrito anteriormente
# F x.("(x)PROP.RESULTS_REVIEW(x[Snomed])" & H y.(!"(y)PROP.PRESCRIBED(y[Snomed])"))
# RESULT_REVIEW# Función and que le pasas un estado y te dice true si es resultado disponible. 
# PRESCRIBED# Función que me dice si un médico ha solicitado una prueba analítica previamente.
def RESULTS_REVIEW(g1):
  
    q = f"""PREFIX snomed: <http://snomed.info/snomed#>\n\n
    ASK WHERE {{\n    
    GRAPH {g1}
      {{ \n       #?caso snomed:notificationType "Results_available" .
       ?caso snomed:undergoes ?aux.
     
      ?aux snomed:reasonForLoop "Results_review" .
            \n    }}\n}}"""
   
    return g.query(q).askAnswer

def PRESCRIBED(g1):

    q = f"""PREFIX snomed: <http://snomed.info/snomed#>\n\n
    ASK WHERE {{\n    
    GRAPH {g1}
      {{ \n  ?caso snomed:undergoes ?proc.
            ?proc snomed:orderType "Diagnostic_test_order"   .
             ?proc snomed:hasComponent ?aux.
            ?aux snomed:testName "Complete_Blood_Count" .
            \n    }}\n}}"""
   
    return g.query(q).askAnswer


def RESULTS_AVAILABLE(g1):

    q = f"""PREFIX snomed: <http://snomed.info/snomed#>\n\n
    ASK WHERE {{\n    
    GRAPH {g1}

      {{ \n      
       
       
            ?caso snomed:hasPlan ?plan.
            ?plan snomed:hasComponent ?aux.
            ?aux snomed:notificationType "Results_available" .
            \n    }}\n}}"""
   
    return g.query(q).askAnswer

#Se pidieron unas pruebas analíticas, están los resultados disponibles, pero el sistema no ha notificado por mail que ya estaban disponibles estos resultados. 
#F x.("(x)PROP.PRESCRIBED(x[Snomed])" & X (!(y.("(y)PROP.RESULTS_AVAILABLE(y[Snomed])")) U z.("(z)PROP.RESULTS_REVIEW(z[Snomed])")))
# F x.(A &  (!B U C))
#  A -> PREscribed
# B -> Notification sent RESULTS_AVAILABLE
# C -> Reviewed results RESULT_REVIEW

#F x.("(x)x[Timestamp]>0")
#El tiempo desde que el medico prescribió una prueba analítica hasta que se revisaron los resultados no es mayor a 48 horas.
# F x.("(x)PROP.PRESCRIBED(x[Snomed])" & F y.("(x,y)PROP.RESULTS_REVIEW(y[Snomed]) and (y[Timestamp] - x[Timestamp]<48*3600)"))
# F x.("(x)PROP.PRESCRIBED(x[Snomed])" & F y.("(y)PROP.RESULTS_REVIEW(y[Snomed])" & "(x,y)(y[Timestamp] - x[Timestamp]<48*3600)")) -> Esta tarde mucho menos
# 1,29,3.33,3.96
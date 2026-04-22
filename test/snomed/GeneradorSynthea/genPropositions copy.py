import os
import time
import gc
import shutil
import textwrap
from pyoxigraph import Store, RdfFormat

# --- CONFIGURACIÓN ---
NGOS_PASOS = (
    ((6, 20), (21, 40), (41, 60), (61, 80))
)

N_TRAZAS = (50, 100, 500, 1000, 5000, 10000, 50000, 100000)




path = "test/snomed/GeneradorSynthea"
path_auto = "test/snomed/GeneradorSynthea/auto"

# Asegurar que la carpeta auto existe al inicio
os.makedirs(path_auto, exist_ok=True)

# ---------------------------------------------
# Funciones
# ---------------------------------------------

def generatePropositions(l1, l2, n):
    nombregrafo = f"log_{n}_{l1}_{l2}"
    codeToAdd = f"""
import sys
from pyoxigraph import Store
import time
# Configuración: La ruta a tu carpeta de base de datos
path_auto = "./test/snomed/GeneradorSynthea/auto"
DB_PATH = f"{{path_auto}}/{nombregrafo}"
    """
    
    codeToAdd = textwrap.dedent(codeToAdd).strip() + "\n\n"
    n_experimento = f"{n}_{l1}_{l2}"
    fichProps = f"{path}/funSyntheaOxy.py"
    newFichProps = f"{path}/my_propositions_{n_experimento}.py"
    
    try:
        with open(fichProps, 'r') as orig, open(newFichProps, 'w') as dest:
            dest.write(codeToAdd)
            for line in orig:
                dest.write(line)
        print(f"Generated: 'my_propositions_{n_experimento}.py'")
    except FileNotFoundError:
        print(f"Error: No se encontró '{fichProps}'")



# ---------------------------------------------
# Ejecución Principal
# ---------------------------------------------

crear = True   # Cambiado a True para que procese
borrar = True  # Cambiado a True para evitar que se llene el disco

with open(f"{path}/tiempos.csv", "w", encoding="utf-8") as f:
    f.write("nEvents,l1,l2,time_seconds\n")

    for nEvents in N_TRAZAS:
        # CORRECCIÓN: Usamos NGOS_PASOS en lugar de LONGS
        for nt in NGOS_PASOS: 
            l1, l2 = nt[0], nt[1]
            
            # 1. Generar el archivo .py correspondiente
            generatePropositions(l1, l2, nEvents)
            
            if crear:
                nombre_grafo = f"log_{nEvents}_{l1}_{l2}"
                DB_PATH = os.path.join(path_auto, nombre_grafo)
                archivo_nq = os.path.join(path_auto, f"{nombre_grafo}.nq")

                print(f"\n=== PROCESANDO: {nEvents} eventos, rango ({l1},{l2}) ===")

                # 2. CARGAR en Oxigraph
                ok_carga = cargar_nq(archivo_nq, DB_PATH)

                if not ok_carga:
                    print("→ Saltando experimento por error en carga.")
                    continue

                # Aquí podrías añadir la llamada a tu lógica de procesamiento/tiempos
                # tiempo_final = ejecutar_logica()
                # f.write(f"{nEvents},{l1},{l2},{tiempo_final}\n")
                
                print("Datos cargados y listos.")
                time.sleep(1)
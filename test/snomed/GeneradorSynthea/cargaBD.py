import os
import time
import subprocess
import gc
import shutil
import signal
import sys
import textwrap
from pyoxigraph import Store, RdfFormat
N_WORKFLOWS=10
LONGS = ((6, 20), (21, 40), (41, 60), (61, 80))
N_TRAZAS = (5, 10, 50, 100, 500, 1000, 5000, 10000)*N_WORKFLOWS
LONGS = ((61, 80),)
N_TRAZAS = (100*N_WORKFLOWS,)
 


             
path = "test/snomed/GeneradorSynthea"
path_auto = "test/snomed/GeneradorSynthea/auto"
DB_PATH = ""

# ---------------------------------------------
# Control del store global para cleanup en Ctrl+C
# ---------------------------------------------
_store_global = None
def generatePropositions(l1, l2, n):
	nombregrafo = f"log_{n}_{l1}_{l2}"
	codeToAdd = f"""
import sys
from pyoxigraph import Store
import time
# Configuración: La ruta a tu carpeta de base de datos
path_auto = "./test/snomed/GeneradorSynthea/auto"
DB_PATH = f"{path_auto}/{nombregrafo}"
    """


	codeToAdd = textwrap.dedent(codeToAdd).strip() + "\n\n"
	
	fichProps = f"{path}/funSyntheaOxy.py"
	newFichProps = f"{path}/my_propositions.py"
	try:
		with open(fichProps, 'r') as orig, open(newFichProps, 'w') as dest:
			dest.write(codeToAdd)

			for line in orig:
				dest.write(line)
		print(f"Generated file 'my_propositions.py' for file '{nombregrafo}'")
	except FileNotFoundError:
		print(f"Error: The source file '{fichProps}' was not found.")
          



def _cleanup(sig, frame):
    global _store_global
    print("\nInterrupción detectada, cerrando store...")
    if _store_global is not None:
        del _store_global
        _store_global = None
        gc.collect()
        time.sleep(1)
    sys.exit(0)

signal.signal(signal.SIGINT, _cleanup)
signal.signal(signal.SIGTERM, _cleanup)


def cargar_nq(archivo_nq, db_path):
    global _store_global

    if not os.path.exists(archivo_nq):
        print(f"Error: '{archivo_nq}' no existe.")
        return False

    try:
        store = Store(db_path)
        _store_global = store

        print(f"Importando {archivo_nq}...")

        with open(archivo_nq, 'rb') as f:
            store.load(f, RdfFormat.N_QUADS)

        print(f"Carga OK. Registros: {len(store)}")

        del store
        _store_global = None
        gc.collect()

        return True

    except Exception as e:
        print(f"Error carga: {e}")
        _store_global = None
        return False


def borrar_db(db_path):
    reintentos = 8

    for intento in range(reintentos):
        try:
            if os.path.exists(db_path):
                shutil.rmtree(db_path)
            print("Grafos borrados, procediendo al siguiente experimento...")
            return
        except PermissionError:
            print(f"PermissionError intento {intento+1}/{reintentos}, esperando...")
            gc.collect()
            time.sleep(3)

    print("ERROR CRÍTICO: No se pudo eliminar la BD.")


# ---------------------------------------------
crear=True
borrar=False
with open(f"{path}/tiempos.csv", "w", encoding="utf-8") as f:
    f.write("nEvents,l1,l2,time_seconds\n")

    for nEvents in N_TRAZAS:
        for nt in LONGS:
           
                  
            if crear:
                nombre_grafo=f"log_{nEvents}_{nt[0]}_{nt[1]}"
                DB_PATH = f"{path_auto}/{nombre_grafo}"
                print(f"\n=== {nEvents} eventos, rango ({nt[0]},{nt[1]}) ===")

                # 1. CARGA en el proceso principal
                ok_carga = cargar_nq(
                    f"{path_auto}/log_{nEvents}_{nt[0]}_{nt[1]}.nq",DB_PATH
                )

                if not ok_carga:
                    print("→ Saltando por error en carga.")
                    borrar_db(DB_PATH)
                    continue

                print("Datos cargados en Oxigraph")
                time.sleep(2)
            

           

            # 3. LIMPIEZA
            if borrar:                
                borrar_db(DB_PATH)
                time.sleep(1)
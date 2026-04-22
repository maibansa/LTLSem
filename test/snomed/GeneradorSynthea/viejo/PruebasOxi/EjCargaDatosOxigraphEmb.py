import sys
import os
from pyoxigraph import Store, RdfFormat

path_auto = "./test/snomed/GeneradorSynthea/auto"
DB_PATH = f"{path_auto}/mi_base_datos_oxigraph"

def cargar_log_nq(archivo_nq):
    if not os.path.exists(archivo_nq):
        print(f"Error: El archivo '{archivo_nq}' no existe.")
        return

    try:
        with Store(DB_PATH) as store:  # <-- with para garantizar cierre
            print(f"Importando {archivo_nq} a la base de datos...")
            with open(archivo_nq, 'rb') as f:
                store.load(f, RdfFormat.N_QUADS)
            print("¡Carga completada con éxito!")
            print(f"Total de registros en la BD: {len(store)}")

    except Exception as e:
        print(f"Error durante la ejecución: {e}")

if __name__ == "__main__":
    args = sys.argv[1:]
    if args:
        cargar_log_nq(args[0])
    else:
        print("Uso: python script.py ruta/al/archivo.nq")
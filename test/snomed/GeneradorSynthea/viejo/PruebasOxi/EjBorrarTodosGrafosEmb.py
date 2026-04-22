import shutil
import os
import time
from pyoxigraph import Store

path_auto = "./test/snomed/GeneradorSynthea/auto"
DB_PATH = f"{path_auto}/mi_base_datos_oxigraph"
DB_PATH2 = f"{path_auto}/mi_base_datos_oxigraph2"


def borrar_carpeta_con_reintentos(path, reintentos=5, espera=2):
    for intento in range(reintentos):
        try:
            if os.path.exists(path):
                shutil.rmtree(path)
                print(f"Carpeta '{path}' eliminada.")
            return
        except PermissionError as e:
            print(f"PermissionError (intento {intento+1}/{reintentos}): {e}")
            time.sleep(espera)
    print(f"ERROR: No se pudo eliminar '{path}' tras {reintentos} intentos.")


def borrar_todo_rapido():
    borrar_carpeta_con_reintentos(DB_PATH)
    borrar_carpeta_con_reintentos(DB_PATH2)

    # Recrear vacía y cerrar inmediatamente
    with Store(DB_PATH) as store:
        pass
    print("Base de datos recreada y vacía.")


if __name__ == "__main__":
    borrar_todo_rapido()
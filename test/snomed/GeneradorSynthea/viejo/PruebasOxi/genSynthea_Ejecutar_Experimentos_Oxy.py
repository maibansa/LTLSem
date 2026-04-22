import os
import textwrap
import time
import requests

LONGS = ((6,20),(21,35),(36,50),(51,65),(66,80))
N_TRAZAS = (50,)

path = "test/snomed/GeneradorSynthea"

path_auto = "test/snomed/GeneradorSynthea/auto"




# ---------------------------------------------
# el fichero de proposiciones ....py solo se diferencia entre unos experimentos y otros en la bbdd con la info semántica
# se puede, a partir de un fichero con todo menos las primeras líneas, generar el específico añadiéndole como primeras
# ---------------------------------------------




with open(f"{path}/tiempos.csv", "w", encoding="utf-8") as f:
    f.write("nEvents,l1,l2,time_seconds\n")

    for nEvents in N_TRAZAS:
        for nt in LONGS:
            # construir el fichero de proposiciones, con las primeras líneas específicas y el resto igual. Se llama "propositions.py"
            # la primera instrucción de "formulas.txt" será "_LOAD PROP propositions.py"
            command = f"python {path}/EjCargaDatosOxigraph.py {path_auto}/log_{nEvents}_{nt[0]}_{nt[1]}.nq"
            os.system(command)
            print("Datos cargados en Oxygraph")           
            
            command = f"python MC.py log-file={path_auto}/log_{nEvents}_{nt[0]}_{nt[1]} interactive=false formula-file={path}/formulas.txt> {path_auto}/log_{nEvents}_{nt[0]}_{nt[1]}_res.txt"
            start = time.perf_counter()
            os.system(command)
            end = time.perf_counter()
            print(f"Experimento con {nEvents} trazas y rango ({nt[0]},{nt[1]}) completado en {end-start:.4f} segundos.")
            f.write(f"{nEvents},{nt[0]},{nt[1]},{end-start:.4f}\n")
            
            command = f"python {path}/EjBorrarTodosGrafos.py"
            os.system(command)
            print("Grafos borrados, procediendo al siguiente experimento...")
            time.sleep(1)
       
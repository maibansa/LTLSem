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

def generatePropositions(l1, l2, n):
	monbreGrafo = f"log_{n}_{l1}_{l2}.nq"
	codeToAdd = f"""
	from rdflib import Dataset
	file_path = f"{path_auto}/{monbreGrafo}"
	g = Dataset()
	g.parse(source=file_path, format="nquads")
	"""

	codeToAdd = textwrap.dedent(codeToAdd).strip() + "\n\n"
	
	fichProps = f"{path}/funSynthea.py"
	newFichProps = f"{path}/my_propositions.py"
	try:
		with open(fichProps, 'r') as orig, open(newFichProps, 'w') as dest:
			dest.write(codeToAdd)

			for line in orig:
				dest.write(line)
		print(f"Generated file 'my_propositions.py' for file ''{monbreGrafo}")
	except FileNotFoundError:
		print(f"Error: The source file '{fichProps}' was not found.")

# ---------------------------------------------
os.makedirs(path, exist_ok=True)

with open(f"{path}/tiempos.csv", "w", encoding="utf-8") as f:
    f.write("nEvents,l1,l2,time_seconds\n")

    for nEvents in N_TRAZAS:
        for nt in LONGS:
            # construir el fichero de proposiciones, con las primeras líneas específicas y el resto igual. Se llama "propositions.py"
            # la primera instrucción de "formulas.txt" será "_LOAD PROP propositions.py"
            generatePropositions(nt[0], nt[1], nEvents)

            command = f"python MC.py log-file={path_auto}/log_{nEvents}_{nt[0]}_{nt[1]} interactive=false formula-file={path}/formulas.txt> {path_auto}/log_{nEvents}_{nt[0]}_{nt[1]}_res.txt"
            start = time.perf_counter()
            os.system(command)
            end = time.perf_counter()
            f.write(f"{nEvents},{nt[0]},{nt[1]},{end-start:.4f}\n")
       
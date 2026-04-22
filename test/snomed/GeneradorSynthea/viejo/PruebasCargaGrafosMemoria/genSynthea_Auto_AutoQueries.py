import subprocess
import os

# --- CONFIGURACIÓN ---
TRABAJO_DIR = "test/snomed/GeneradorSynthea"
TEMPLATE_INIT = os.path.join(TRABAJO_DIR, "input.txt")
AUTO_DIR = os.path.join(TRABAJO_DIR, "auto")
MC_PY = "MC.py"

LISTA_NUM_TRACES = [5, 10, 50, 100, 500, 1000]
RANGOS_PASOS = [(6, 20), (21, 35), (36, 50), (51, 65), (66, 80)]

if not os.path.exists(AUTO_DIR):
    os.makedirs(AUTO_DIR)

def ejecutar_experimentos():
    if not os.path.exists(TEMPLATE_INIT):
        print(f"❌ Error: No encuentro la plantilla {TEMPLATE_INIT}")
        return

    with open(TEMPLATE_INIT, 'r', encoding='utf-8') as f:
        template_content = f.read()

    for n_traces in LISTA_NUM_TRACES:
        for inicio, fin in RANGOS_PASOS:
            tag = f"log_{n_traces}_{inicio}_{fin}"
            
            # Rutas
            log_file_path = f"{AUTO_DIR}/{tag}"
            temp_init_path = f"{AUTO_DIR}/{tag}.init"
            output_res = f"{AUTO_DIR}/{tag}_res.txt"
            
            # Sustitución de @@@
            nuevo_contenido = template_content.replace("@@@", tag)
            
            with open(temp_init_path, "w", encoding='utf-8') as f_temp:
                f_temp.write(nuevo_contenido)
            
            # Comando
            comando = [
                "python", MC_PY,
                f"log-file={log_file_path}",
                f"init-file={temp_init_path}"
            ]
            
            print(f"Ejecutando: {tag}...", end=" ", flush=True)
            
            try:
                # 'stderr=subprocess.STDOUT' mezcla errores y salida en el mismo sitio
                with open(output_res, "w", encoding='utf-8') as out_f:
                    subprocess.run(comando, stdout=out_f, stderr=subprocess.STDOUT, text=True, check=True)
                print("✅ OK")
            except subprocess.CalledProcessError:
                print("❌ ERROR (Mira el archivo _res.txt)")

if __name__ == "__main__":
    ejecutar_experimentos()
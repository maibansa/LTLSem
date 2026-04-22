import requests
import sys

# Configuración
URL_OXY = "http://localhost:7878/store"
#ARCHIVO_NQ = "log_50_6_20.nq"

def cargar_log_nq(ARCHIVO_NQ):
    try:
        with open(ARCHIVO_NQ, 'rb') as f:
            # Definimos el header para N-Quads
            headers = {'Content-Type': 'application/n-quads'}
            
            print(f"Subiendo {ARCHIVO_NQ} a Oxygraph...")
            response = requests.post(URL_OXY, data=f, headers=headers)
            
        if response.status_code in [200, 201, 204]:
            print("¡Carga completada con éxito!")
        else:
            print(f"Error en la carga: {response.status_code}")
            print(response.text)
            
    except FileNotFoundError:
        print("El archivo no existe.")
    except requests.exceptions.ConnectionError:
        print("No se pudo conectar con el servidor Oxygraph. ¿Está encendido?")


if __name__ == "__main__":
    args = sys.argv[1:]
    if args:
        ARCHIVO_NQ = args[0]
        cargar_log_nq(ARCHIVO_NQ)

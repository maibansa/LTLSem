import requests

URL_UPDATE = "http://localhost:7878/update"

def borrar_todo():
    # La sentencia 'DROP ALL' elimina todos los grafos del sistema
    # 'CLEAR ALL' también funciona, pero DROP es más radical
    query_borrado = "DROP ALL"
    
    try:
        # Nota: Usamos el endpoint /update, no /query ni /store
        response = requests.post(URL_UPDATE, data={'update': query_borrado})
        
        if response.status_code in [200, 204]:
            print("Base de datos vaciada: Todos los grafos han sido eliminados.")
        else:
            print(f"Error al borrar: {response.status_code}")
            print(response.text)
            
    except requests.exceptions.ConnectionError:
        print("Error de conexión con el servidor.")
if __name__ == "__main__":       
    borrar_todo()


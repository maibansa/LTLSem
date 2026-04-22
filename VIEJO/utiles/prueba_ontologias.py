from rdflib import Graph, RDF, RDFS, OWL, XSD

# Cargar ontología
g = Graph()
g.parse("../semantic_logs/segitour.owl", format="xml")

# Construir diccionario propiedad -> rango (como string)
property_ranges = {}
for prop in g.subjects(RDF.type, OWL.DatatypeProperty):
    rango = g.value(prop, RDFS.range)
    if rango is not None:
        property_ranges[str(prop)] = str(rango)


def cast_value(prop_uri, value_str):
    rango = property_ranges.get(prop_uri)
    if rango is None:
        return value_str

    if rango == "xsd:integer":
        return int(value_str)
    elif rango == "xsd:boolean":
        val_lower = value_str.lower()
        if val_lower in ("true", "1"):
            return True
        elif val_lower in ("false", "0"):
            return False
        else:
            raise ValueError(f"Valor booleano inválido: {value_str}")
    elif rango == "xsd:date":
        # Espera formato ISO 8601: 'YYYY-MM-DD'
        try:
            return datetime.strptime(value_str, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError(
                f"Formato de fecha inválido: {value_str}, se esperaba 'YYYY-MM-DD'")
    else:
        return value_str


# Mostrar diccionario para verificar
print("Diccionario propiedades y rangos:")
for k, v in property_ranges.items():
    print(f"{k} --> {v}")

# Ejemplo de casteo
prop = "estur:resultCount"  # URI completa
val = "6"

try:
    casted_val = cast_value(prop, val)
    print(f"\nValor original: '{val}'")
    print(f"Valor casteado: {casted_val} (tipo: {type(casted_val)})")
except Exception as e:
    print(f"Error: {e}")

    asignatura de Metodologías ágiles de calidad

from rdflib import Dataset, URIRef, Namespace

file_path = "test/ontotour/ontoej.nq"
g = Dataset()
g.parse(source=file_path, format="nquads")

# Ver qué hay en L8
print("=== CONTENIDO DE L8 ===")
l8_graph = g.graph(URIRef("http://example.org/event/L8"))
for s, p, o in l8_graph:
    print(f"{s.split('/')[-1]} -> {p.split('#')[-1] if '#' in str(p) else p.split('/')[-1]} -> {o}")

from rdflib import Dataset

file_path = "test/ontotour/ontoej.nq"
g = Dataset()
g.parse(source=file_path, format="nquads")

# Listar todos los grafos disponibles
print("=== GRAFOS DISPONIBLES ===")
for graph in g.graphs():
    print(f"Grafo: {graph}")

print("\n=== TESTEO FINAL_CONFIRMATION ===")
q = """PREFIX ontotour: <http://ontotour.org/ontology#>

ASK WHERE {
    GRAPH <http://example.org/event/L8> {
        ?proc <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://snomed.info/id/722420007> .
        ?proc ontotour:evaluationMethod "Double_Step_Verification_UI" .
    }
}"""
result = g.query(q)
print(f"FINAL_CONFIRMATION (L8): {result.askAnswer}")

print("\n=== TESTEO IDENTITY_DOCUMENT_UPLOADED ===")
q2 = """PREFIX ontotour: <http://ontotour.org/ontology#>

ASK WHERE {
    GRAPH <http://example.org/event/L10> {
        ?finding ontotour:storagePath ?path .
        FILTER(STRSTARTS(STR(?path), "s3://travel-docs/")) .
    }
}"""
result2 = g.query(q2)
print(f"IDENTITY_DOCUMENT_UPLOADED (L10): {result2.askAnswer}")

print("\n=== TESTEO UPSELL_ADDED ===")
q3 = """PREFIX ontotour: <http://ontotour.org/ontology#>

ASK WHERE {
    GRAPH <http://example.org/event/L6> {
        ?proc ontotour:hasFocus ?finding .
        ?finding ontotour:actionType "Upsell_Selection" .
    }
}"""
result3 = g.query(q3)
print(f"UPSELL_ADDED (L6): {result3.askAnswer}")

print("\n=== CONFIRMEMOS REVIEW ===")
q4 = """PREFIX ontotour: <http://ontotour.org/ontology#>

ASK WHERE {
    GRAPH <http://example.org/event/L2> {
        ?case ontotour:executes ?proc .
        ?proc ontotour:searchMethod "Multimodal_Search_Engine" .
    }
}"""
result4 = g.query(q4)
print(f"REVIEW (L2): {result4.askAnswer}")

#!/usr/bin/env bash

set -euo pipefail

# 1. Lista de N_TRAZAS
N_TRAZAS=(50 500 1000 5000 10000)

# 2. Parejas de longitudes
LONGS=(
  "6,20"
  "21,35"
  "36,50"
  "51,65"
  "66,80"
)

for n in "${N_TRAZAS[@]}"; do
  for pair in "${LONGS[@]}"; do

    # Extraemos MIN y MAX
    IFS=',' read -r MIN MAX <<< "$pair"

    echo
    echo "========================================================"
    echo "PROCESANDO: N=$n | Rango: $MIN a $MAX"
    echo "========================================================"

    ORIGEN="test/snomed/GeneradorSynthea/my_propositions_${n}_${MIN}_${MAX}.py"
    DESTINO="test/snomed/GeneradorSynthea/my_propositions.py"

    if [[ -f "$ORIGEN" ]]; then
      echo "[INFO] Copiando $ORIGEN a $DESTINO..."
      cp -f "$ORIGEN" "$DESTINO"

      echo "[EXEC] Ejecutando MC.py para log_${n}_${MIN}_${MAX}..."
      python3 MC.py \
        log-file="test/snomed/GeneradorSynthea/auto/log_${n}_${MIN}_${MAX}" \
        interactive=false \
        formula-file="test/snomed/GeneradorSynthea/formulas.txt"
    else
      echo "[ERROR] No se encontró el archivo: $ORIGEN"
    fi

  done
done

echo
echo "=== Proceso finalizado ==="

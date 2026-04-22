@echo off
setlocal enabledelayedexpansion

:: 1. Lista de N_TRAZAS actualizada
set N_TRAZAS=50 500 1000 5000 10000

:: 2. Parejas de longitudes
set LONGS="6,20" "21,35" "36,50" "51,65" "66,80"

for %%n in (%N_TRAZAS%) do (
    for %%l in (%LONGS%) do (
        
        :: Extraemos los valores l1 y l2 de la pareja actual
        :: Quitamos las comillas del string para el comando for /f
        set "pair=%%~l"
        for /f "tokens=1,2 delims=," %%a in ("!pair!") do (
            set MIN=%%a
            set MAX=%%b
        )

        echo.
        echo ========================================================
        echo PROCESANDO: N=%%n ^| Rango: !MIN! a !MAX!
        echo ========================================================

        set ORIGEN=test\snomed\GeneradorSynthea\my_propositions_%%n_!MIN!_!MAX!.py
        set DESTINO=test\snomed\GeneradorSynthea\my_propositions.py

        if exist "!ORIGEN!" (
            echo [INFO] Copiando !ORIGEN! a !DESTINO!...
            copy /y "!ORIGEN!" "!DESTINO!" >nul
            
            echo [EXEC] Ejecutando MC.py para log_%%n_!MIN!_!MAX!...
            python MC.py log-file=test\snomed\GeneradorSynthea\auto\log_%%n_!MIN!_!MAX! interactive=false formula-file=test\snomed\GeneradorSynthea\formulas.txt
        ) else (
            echo [ERROR] No se encontro el archivo: !ORIGEN!
        )
    )
)

echo.
echo === Proceso finalizado ===
pause
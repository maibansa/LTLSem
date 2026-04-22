@echo off
setlocal enabledelayedexpansion

:: Lista de N_TRAZAS
set N_TRAZAS=50
:: IMPORTANTE: Parejas entre comillas para que no se rompan por la coma
set LONGS="6,20" "21,35" "36,50" "51,65" "66,80"

for %%n in (%N_TRAZAS%) do (
    for %%l in (%LONGS%) do (
        
        :: Quitamos las comillas y extraemos valores
        for /f "tokens=1,2 delims=," %%a in (%%l) do (
            set MIN=%%a
            set MAX=%%b
        )

        echo --------------------------------------------------------
        echo PROCESANDO: N=%%n ^| MIN=!MIN! ^| MAX=!MAX!
        echo --------------------------------------------------------

        set ORIGEN=test\snomed\GeneradorSynthea\my_propositions_%%n_!MIN!_!MAX!.py
        set DESTINO=test\snomed\GeneradorSynthea\my_propositions.py

        if exist "!ORIGEN!" (
            copy /y "!ORIGEN!" "!DESTINO!"
            
            python MC.py log-file=test\snomed\GeneradorSynthea\auto\log_%%n_!MIN!_!MAX! interactive=false formula-file=test\snomed\GeneradorSynthea\formulas.txt
        ) else (
            echo [ERROR] No existe: !ORIGEN!
        )
    )
)

pause
"""
--------------------------------------------------------------------
File:    MC.py
Author: Joaquín Ezpeleta (Univ. of Zaragoza, Spain)
Date:    October 2025
         Model checker based on the DLTL logic.
Parallelized version using pathos and itertools.
------------------------------------------------------------------
"""
import DLTL
import parser
import my_propositions as PROP
import log_handling as LH

import time
import sys
import traceback
import re
import os
import itertools
from typing import Any

# Use pathos for serialization of dynamically generated functions
from pathos.multiprocessing import ProcessingPool as Pool

# ---------------------------------------
# Global stores
results = dict()       
countResults = dict()  
checkedForms = []      
macros = dict()

# ---------------------------------------
# WORKER FUNCTION (Must be at top-level)
# ---------------------------------------
def worker_evaluate_trace(id_, trace, compiledFormula):
    """
    Evaluates the formula on a single trace.
    This runs in a separate process.
    """
    res = compiledFormula(trace)
    cumple, _, _, media = DLTL.results_statistics(res)
    return id_, cumple, media

# ---------------------------------------
# Input Handling
# ---------------------------------------
def read_formule(interactive: bool, prompt: str) -> str:
    try:
        if interactive:
            f = input(prompt)
        else:
            f = input()
        if f != "" and f[0] != ';':
            return f
        return ""
    except EOFError:
        return "_AGUR"
    except Exception:
        return "_AGUR"

def multi_line_input() -> str:
    lines = []
    while True:
        try:
            line = input()
            if '$' in line:
                lines.append(line.split('$')[0])
                break
            lines.append(line)
        except EOFError:
            break
    return ''.join(lines)

def multi_line_read_formule(interactive: bool, prompt: str) -> str:
    if interactive:
        sys.stdout.write(prompt)
        sys.stdout.flush()
    s = multi_line_input()
    return s if (s and s[0] != ';') else ""

# ---------------------------------------
# Core Checker Logic
# ---------------------------------------
def check(dictParameters: dict[str, Any]) -> None:
    startTime = time.time()
    logData = LH.load_mod(dictParameters['log-file'])
    print(f"Loading time: {time.time() - startTime:.4f} seconds")

    LH.print_info_log(logData)
    LH.save_trace_lengths(logData)

    for id_ in logData['sortedIDs']:
        results[id_] = f"{id_}"
        countResults[id_] = f"{id_}"

    prompt = "DLTL -> " if dictParameters['interactive'] else ""

    # Macro Case Handlers
    def case_info(): LH.print_info_log(logData)
    def case_write(): LH.save_results(logData, results, countResults, checkedForms)
    def case_who(): print(f"{LH.who(logData, results)}")
    def case_who_not(): print(f"{LH.who_not(logData, results)}")
    
    def starts_with_interrogation(varName: str) -> bool:
        if not varName or varName[0] != '?':
            print(f"Macro names must start with '?'", file=sys.stderr)
            return False
        return True

    def case_set(varName: str, pars: str):
        if starts_with_interrogation(varName):
            macros[varName] = tuple([a.strip() for a in pars.split(',')])

    def case_re(varName: str, pars: str):
        if starts_with_interrogation(varName):
            macros[varName] = tuple(a for a in logData['atomics'] if re.fullmatch(pars, a))

    def case_range(varName: str, pars: str):
        if starts_with_interrogation(varName):
            limits = pars.split(',')
            init, fin = int(limits[0]), int(limits[1])
            step = 1 if len(limits) <= 2 else int(limits[2])
            macros[varName] = tuple(str(v) for v in range(init, fin+1, step))

    def case_clear_data():
        for id_ in logData['sortedIDs']:
            results[id_] = f"{id_}"
            countResults[id_] = f"{id_}"

    macroCases = {
        "_INFO": case_info, "_WRITE": case_write, "_WHO": case_who,
        "_WHO_NOT": case_who_not, "_SET": case_set, "_RE": case_re,
        "_RANGE": case_range, "_CLEAR_DATA": case_clear_data,
        "_BYE": lambda: sys.exit(), "agur": lambda: sys.exit()
    }

    def evaluate_formula(form: str, pool: Pool) -> None:
        if not form or form[0] == ';': return
        
        try:
            command, _, remainder = form.partition(' ')

            if command in macroCases:
                if command in ('_SET', '_RE', '_RANGE'):
                    varName, _, rest = remainder.partition(' ')
                    macroCases[command](varName, rest)
                else:
                    macroCases[command]()
            else:
                formulas_to_eval = LH.unfold_macros(form, macros)

                for f in formulas_to_eval:
                    iterStartTime = time.time()
                    parsedFormula = parser.parse_expression(f)
                    checkedForms.append(f)
                    compiledFormula = DLTL.eval_formula(parsedFormula)

                    # --- Parallel Processing ---
                    # We prepare the lists to pass to the pool
                    ids = list(logData['traces'].keys())
                    traces = [logData['traces'][id_] for id_ in ids]
                    
                    # map(func, list1, list2, list3) will zip them together.
                    # itertools.repeat avoids making a physical list of the function pointer.
                    worker_results = pool.map(
                        worker_evaluate_trace, 
                        ids, 
                        traces, 
                        itertools.repeat(compiledFormula)
                    )

                    # --- Result Aggregation ---
                    yes = 0
                    for id_, cumple, media in worker_results:
                        yes += cumple
                        results[id_] += ',' + str(cumple)
                        countResults[id_] += ',' + str(media)

                    roundedTime = round(time.time() - iterStartTime, 2)
                    n = logData['nTraces']
                    perc = round(100 * yes / n, 2) if n > 0 else 0.0
                    print(f"{yes},{n-yes},{perc},{roundedTime}")

        except Exception:
            traceback.print_exc(file=sys.stderr)

    # Use os.cpu_count() or set a fixed number of workers (e.g., Pool(4))
    with Pool(os.cpu_count()) as pool:
        # Process Init File
        if dictParameters['init-file']:
            try:
                with open(dictParameters['init-file'], 'r') as file:
                    for line in file:
                        evaluate_formula(line.strip().replace("'", "\\'"), pool)
            except Exception as e:
                print(f"Init error: {e}", file=sys.stderr)

        # Main Loop
        while True:
            s = dictParameters['formula-input-func'](dictParameters['interactive'], prompt)
            if s is None or s == "_AGUR": break
            evaluate_formula(s.replace("'", "\\'"), pool)

# ---------------------------------------
# Program Entry
# ---------------------------------------
def main(argv):
    dictMainPars = {
        'formula-file': "", 'log-file': "", 'init-file': "",
        'interactive': True, 'formula-input-func': None, 'multi-line': False
    }

    for arg in argv[1:]:
        if '=' in arg:
            k, v = arg.split('=', 1)
            dictMainPars[k] = v

    dictMainPars['interactive'] = str(dictMainPars['interactive']).lower() != 'false'
    dictMainPars['formula-input-func'] = multi_line_read_formule if str(dictMainPars['multi-line']).lower() == 'true' else read_formule

    if not dictMainPars['log-file']:
        print("Error: log-file=<filename> is required.", file=sys.stderr)
        sys.exit(1)

    check(dictMainPars)
# ---------------------------------------
if __name__ == "__main__":
    main(sys.argv)
    
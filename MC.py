"""
--------------------------------------------------------------------
File:   MC.py
Author: Joaquín Ezpeleta (Univ. of Zaragoza, Spain)
Date:   October 2025
        Model checker based on the DLTL logic and algorithm in the following reference:
        J. M. Couvreur, J. Ezpeleta
        "A Linear Temporal Logic Model Checking Method over Finite Words with Correlated Transition Attributes" 
        Procs. of the 7th International Symposium on Data-driven Process Discovery and Analysis (SIMPDA 2017),
        Neuchâtel, Switzerland, December 6-8, 2017, ISSN: 1613-0073, Lecture Notes in Business Information Processing,
        Vol. 340, Springer, Paolo Ceravolo, Maurice van Keulen and Kilian Stoffel (Eds.), 2019 
Coms:   Prototype for TACAS artifacts
------------------------------------------------------------------
"""
import DLTL
import parser
import my_propositions as PROP
import log_handling as LH
import time
import sys, os
import traceback
import re
import argparse
import time

import importlib.util
from types import ModuleType
from pathlib import Path
import inspect

from typing import TypeAlias, Tuple, Any, List
# ---------------------------------------
# to store the checking results
results = dict()  # id,1,0,1,0,0, ...
countResults = dict()  # id,3,0,15,2,17, ...
checkedForms = [] #to store the evaluated formulas
# ---------------------------------------
# The keys will be of the form ?activities, and the content will be a set of propositional variables:
# ?activities: (load, mark, unload)
# When an input formula contains ?activities, it will generate three formulas.
# For example, the formula "F ?activities" will generate the formulas:
# "F load", "F mark", "F unload"
macros = dict()
# ---------------------------------------
def read_formule(interactive: bool, prompt: str) -> str:
    try:
        if interactive:
            f = input(prompt)
        else:
            f = input()
        if f != "" and f[0] != ';':
            return f
        else:
            return ""
    except EOFError:
        print(f"EOF found when reading formula", file=sys.stderr)
        return "_AGUR"
    except Exception as e:
        print(f"Unexpected error reading formula: {e}", file=sys.stderr)
        return "_AGUR"
# ---------------------------------------
def multi_line_input() -> str:
    lines = []
    theEnd = False
    while not theEnd:
        line = input()
        if '$' in line:
            lines.append(line.split('$')[0])
            theEnd = True
        else:
            lines.append(line)
    return ''.join(lines)
# ---------------------------------------
def multi_line_read_formule(interactive: bool, prompt: str) -> str:
    if interactive:
        sys.stdout.write(prompt)
    s = multi_line_input()
    if s and s[0] != ';': #;: the line is a comment
        return s
    else:
        return ""
# ---------------------------------------
# dictMainPars = {
#     'formula-file': "" or path to the formula file
#     'log-file': path to the model file, without the ".mod" extension
#     'init-file': "" or path to the init file
#     'interactive': True|False
#     'formula-input-func': function to read the formula (multi-line or single-line)
# }
def check(dictParameters: dict[str, Any]) -> None:
    # TODO: generalizar
    startTime = time.time()
    logData = LH.load_mod(dictParameters['log-file'])

    endTime = time.time()
    #print(f"Loading time: {endTime - startTime:.4f} seconds")

    #LH.print_info_log(logData)
    LH.save_trace_lengths(logData)

    for id in logData['sortedIDs']:
        results[id] = f"{id}"
        countResults[id] = f"{id}"

    prompt = "DLTL -> " if dictParameters['interactive'] else ""

    if dictParameters['formula-file']:
        try:
            sys.stdin = open(dictParameters['formula-file'], "r")
        except FileNotFoundError:
            print(f"Error: Formula file '{dictParameters['formula-file']}' was not found.", file=sys.stderr)
        except Exception as e:
            print(f"An unexpected error occurred: {e}", file=sys.stderr)
    # ---------------------------------------------
    def case_info() -> None:
        LH.print_info_log(logData)
    # ---------------------------------------------
    def case_write() -> None:
        LH.save_results(logData, results, countResults, checkedForms)
    # ---------------------------------------------
    def case_who() -> None:
        print(f"{LH.who(logData, results)}")
    # ---------------------------------------------
    def case_who_not() -> None:
        print(f"{LH.who_not(logData, results)}")
    # ---------------------------------------------
    # macro names must start with '?'
    def starts_with_interrogation(varName: str) -> bool:
        if not varName[0] == '?':
            print(f"'{varName}' is not acceptable as a macro name", file=sys.stderr)
            print(f"The name of a macro must start with '?'", file=sys.stderr)
            print(f"Try ?{varName}", file=sys.stderr)
            return False
        else:
            return True
    # ---------------------------------------------
    # _SET ?NB2 'X2','X7','X12','X17','X22','X27','X32','X37','X42','X47','',''
    def case_set(varName: str, pars: str) -> None:
        if starts_with_interrogation(varName):
            macros[varName] = tuple([a.strip() for a in pars.split(',')]) #strip() for "a   ,   b,   c"  cases
    # ---------------------------------------------
    # _RE ?ac ac_.+
    def case_re(varName: str, pars: str) -> None:
        if starts_with_interrogation(varName):
            er = pars
            macros[varName] = \
                tuple(a for a in logData['atomics'] if re.fullmatch(er, a) is not None)
    # ---------------------------------------------
    # _RANGE ?ar 1,10 [,2]
    def case_range(varName: str, pars: str) -> None:
        if starts_with_interrogation(varName):
            limits = pars.split(',')

            init, fin = int(limits[0]), int(limits[1])
            step = 1 if not len(limits) > 2 else int(limits[2])
            macros[varName] = \
                tuple(str(v) for v in range(init, fin+1, step))
    # ---------------------------------------------
    # moduleName: will be the name of the module
    # funcFile: will be the name of the file with python functions and vars
    # Loads python funcs and vars from "funcFile", creates and add a module
    # "moduleName", and return it
    def case_load(moduleName: str, funcFile: str) -> None:
        spec = importlib.util.spec_from_file_location(moduleName, funcFile)
        module = importlib.util.module_from_spec(spec)
        sys.modules[moduleName] = module
        spec.loader.exec_module(module)
        return module

    # ---------------------------------------------
    def case_clear_data() -> None:
        for id in logData['sortedIDs']:
            results[id] = f"{id}"
            countResults[id] = f"{id}"
    # ---------------------------------------------
    # _BYE
    def case_bye() -> None:
        sys.exit()
    # ---------------------------------------------
    macroCases = {
        "_INFO": case_info,
        "_WRITE": case_write,
        "_WHO": case_who,
        "_WHO_NOT": case_who_not,
        "_SET": case_set,
        "_LOAD": case_load,
        "_RE": case_re,
        "_RANGE": case_range,
        "_CLEAR_DATA": case_clear_data,
        "_BYE": case_bye,
        "agur": case_bye #old things
    }
    # ---------------------------------------------
    def evaluate_formula(form):
        if form and form[0] == '@': #system call
            os.system(form[1:])
        elif form and not form[0] == ';':
            try:
                command, _, remainder = form.partition(' ') 

                if command in ('_WRITE', '_BYE', 'agur', '_INFO', '_WHO', '_CLEAR_DATA', '_AGUR'):
                    macroCases[command]()
                elif command in ('_SET', '_RE', '_RANGE'):
                    varName, _, rest = remainder.partition(' ')
                    macroCases[command](varName, rest)
                elif command in ('_LOAD'):
                    moduleName, _, fileName = remainder.partition(' ')
                    # load the file and creates a new module
                    # Remove quotes from fileName if present
                    fileName = fileName.strip().strip('\'"')
                    newModule = macroCases[command](moduleName.strip(), fileName)
                    # incorporate the new module to DLTL, so that the new funcs
                    # and vars can be used in new formulas
                    DLTL.importNewModule(moduleName,newModule)
                else:
                    formulas = LH.unfold_macros(form, macros)

                    for f in formulas:
                        start_time = time.time()
                        form = parser.parse_expression(f.strip(' '))
                        # fichForms.write(f'{f}\n')
                        checkedForms.append(f)

                        yes = 0
                        for id in logData['traces']:
                            res = DLTL.eval_formula(form, logData['traces'][id])
                            cumple, trueCount, falseCount, media = DLTL.results_statistics(res)
                            yes += cumple
                            results[id] += ',' + str(cumple)
                            countResults[id] += ',' + str(media)
                        roundeTime = round(time.time() - start_time, 2)
                        roundedPercentage = round(100*yes/logData['nTraces'], 2)
                        print(
                            f"{yes},{logData['nTraces']-yes},{roundedPercentage},{roundeTime}")
            except Exception as e:
                print(f"An error occurred: {e}", file=sys.stderr)
                print("\n--- Full Traceback ---", file=sys.stderr)
                traceback.print_exc(file=sys.stdout)
                print("----------------------\n", file=sys.stderr)
    # ---------------------------------------------
    # Is there a "init" file?
    if dictParameters['init-file']:
        fileName = dictParameters['init-file']
        try:
            with open(fileName, 'r') as file:
                for line in file:
                    line = line.replace("'", "\\'").strip()
                    evaluate_formula(line)
        except FileNotFoundError:
            print(f"Error: Init file '{fileName}' was not found.", file=sys.stderr)
        except Exception as e:
            print(f"An unexpected error occurred: {e}", file=sys.stderr)
    # ---------------------------------------------
    while True:
        s = dictParameters['formula-input-func'](dictParameters['interactive'], prompt)

        #quote ' if they appear
        s = s.replace("'", "\\'").strip()
        evaluate_formula(s)
# ---------------------------------------
def main(argv):
    dictMainPars = {
        'formula-file': "",
        'log-file': "",
        'init-file': "",
        'interactive': True,
        'formula-input-func': None,
        'multi-line': False
    }

    for i in range(1,len(argv)): #argv[0] is the program name
        values = argv[i].split('=')
        if len(values) > 1:
            dictMainPars[values[0]] = values[1]

    dictMainPars['interactive'] = not dictMainPars['interactive'] == 'false'
    dictMainPars['formula-input-func'] = multi_line_read_formule if dictMainPars['multi-line'] == 'true' else read_formule

    check(dictMainPars)

# ---------------------------------------
MENS_INVOC = """
USAGE:
    python MC.py [parameters]

PARAMETERS:
    - If no parameters are provided, this help message is shown.
    - Parameters must be in the format: key=value, separated by spaces.
    
    ----------------------------------------------------------------
    REQUIRED:
    ----------------------------------------------------------------
    log-file=<filename>    The name of the log file (without the .mod suffix).
                           Example: log-file=system_trace                    
    ----------------------------------------------------------------
    OPTIONAL:
    ----------------------------------------------------------------
    multi-line=<true|false>       Allows formulas to span multiple lines.
                                  Use $ char to terminate the formula
                                  (Default: false)                               
    interactive=<true|false>      Starts the model checker in interactive mode.
                                  (Default: true)                          
    init-file=<path>              Path to a file containing initial setup commands.
                                  Must include the file suffix/extension.
                                  (Default: "")                          
    formula-file=<path>           Path to a file containing DLTL formulas to check.
                                  Must include the file suffix/extension.
                                  (Default: "")
================================================================================
"""
if __name__ == "__main__":
    if sys.argv == None or len(sys.argv) < 2:
        print(f"{MENS_INVOC}", file=sys.stderr)
        sys.exit
    else:
        main(sys.argv)
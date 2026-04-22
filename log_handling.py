
"""
---------------------------------------------------------------------------
File:   log_handling.py
Author: J. Ezpeleta
Date:   October-2025
Coms:   Prototype for TACAS artifacts
        Invoke as
           python log_handling.py <fich_mod_wo_ext>

        File "<fich_mod_swo_ext>.mod" must the log model

        aE,nV,@att,$p
        id1,c
        id1,a&1&a;1&a=1;b=2
        id1,b&1&a;2&a=1;b=2
        ...
Coms:   Prototype for TACAS artifacts    
---------------------------------------------------------------------------
"""
import os
import sys
import re
import pprint
import csv, io
import DLTL as MC

from typing import Tuple, Any, List, Dict, Set, Union

# Try to import TypeAlias for Python 3.10+, fallback for older versions
try:
    from typing import TypeAlias
except ImportError:
    TypeAlias = None

# ---------------------------------------
# alias
if TypeAlias:
    event: TypeAlias = Tuple[Set[str], ...]
    trace: TypeAlias = Tuple[event]
    logInfo: TypeAlias = Dict[str, Any]
else:
    event = Tuple[Set[str], ...]
    trace = Tuple[event]
    logInfo = Dict[str, Any]
#     nTraces: int
#     nEvents: int
#     atomics: Set[str]
#     traceLengths: Dict[str, int]
#     sortedIDs: List[str]
#     traces: Dict[str, trace]
#     path: str
#     attrib_desc: List[str] 
# ---------------------------------------
ID_SEP = ','
ATRIB_SEP = '&'
VALS_SEP = ';'
SUF_MOD = '.mod'

I_POS = 0 #index 0 of an event will store the pos of the event in the trace
I_ATOM = 1 #index 1 of an event will store the set of atomics in the event

FIRST_EVENT_INDEX = 1 #first line contains the header

# global variable to keep the IDs ordered, and use it when saving results
IDS = []

# Each column name, "name", not being of an atomic proposition, will generate
# a variable with the name "name" whose value is the index in the event tuple corresponding
# to that column. This is so because all the atomic colums are stored in the first component
# of the tuple, while those that are not atomic will be stored in consecutive positions.
# For instace, if the colums are of types "a,n,a,a,s" and the column name are "n1,n2,n3,n4,n5",
# those with type "a" will go to position 0, while "n2" and "n5" will be at positions 1 and 2, resp.
# Therefore, mapIndexNonAtomic['n2'] = 2
mapIndexNonAtomic = dict()

# ---------------------------------------
# index generator for columns with non-atomic values
# index 0: pos in the event tuple to store pos of the event in the trace
# index 1: pos of the set of event atomics
nextIndex = 1
def nextIndexNonAtomic() -> int:
    global nextIndex
    nextIndex += 1
    return nextIndex
# ---------------------------------------
# format in {'n', 's', 'b'}
# cast the string as either float, bool or string, depending on "format"
def cast_format(value_str: str, format: str) -> Union[bool, float, str]:
    val = value_str.strip()

    if format == 'n':
        try:
            val = float(val)
        except Exception as e:
            print(f"Bad numeric format. Asigning 0.0: {e}", file=sys.stderr)
            val = 0.0
        return val
    elif format == 'b':
        if val == '':
            return False
        else:
            if val.lower() == 'true':
                return True
            elif val.lower() == 'false':
                return False
    else: #format == 's'
        return val

# cast the string as either float, bool or string, depending on the content
def cast(value_str: str) -> Union[bool, float, str]:
    val = value_str.strip()

    # bool
    if val.lower() == 'true':
        return True
    elif val.lower() == 'false':
        return False

    # int or float as float
    try:
        return float(val)
    except ValueError:
        pass

    # it is just a string
    return val
# ---------------------------------------
# Converts a string into a valid Python identifier
def to_valid_identifier(s: str) -> str:
    # Replace non-word chars with _
    s = re.sub(r'\W|^(?=\d)', '_', s)
    return s
# ---------------------------------------
# formats: (a,n,@,$)
# fieldNames: (E,V,att,p)
# valsAtribs: [a, 4, "a;1", "a=1;b=2"]
# line: line of the event
# Generates the event strucure as a tuple of the form
# (-1,set('a'), 4, set('a','1'), dict('a':1,'b':2))

def generate_event(formats: Tuple[str, ...], fieldNames: Tuple[str, ...], 
                   valsAtribs: List[str], line: int) -> event:
    # create an empty event as a list, whose first el is the set for 
    # attributes in the event
    eventStr = [-1,set()] #-1: pos of the event in the trace; set(): to store atomics
    for f in formats:
        if f == '@':  # a set of strings
            eventStr.append(set())
        elif f == '$':  # a dictonary, k1=v1;k2=v2; ....
            eventStr.append(dict())
        elif f == 'a':  # an atomic, will be stored in eventStr[I_ATOM], already created
            pass
        else: #place for scalar primitive types: int, bool, float, ....
            eventStr.append(None)

    return generate_tuple_event(formats, fieldNames, valsAtribs, line, eventStr)

# ---------------------------------------
# the event is semantically correct wrt the log structure
# the structure to store the event information has been created when invoking,
# being eventStr[I_ATOM] the set of atomics
def generate_tuple_event(formats: Tuple[str, ...], fieldNames: Tuple[str, ...], 
                         valsAtribs: List[str], line: int, 
                         eventStr: List[Any]) -> event:
    # there will have as many elements as formats, plus 1 for atomics
    # Insert attribute values into the structure
    for i in range(len(formats)):
        if formats[i] == 'a':
            eventStr[I_ATOM].add(valsAtribs[i]) #atomic proposition
        elif formats[i] in ('n', 's', 'b'):
            eventStr[mapIndexNonAtomic[fieldNames[i]]] = cast_format(valsAtribs[i], formats[i])
        elif formats[i] == '@': #set
            for v in valsAtribs[i].split(VALS_SEP):
                eventStr[mapIndexNonAtomic[fieldNames[i]]].add(v.strip())
        elif formats[i] == '$': #dict
            for v in valsAtribs[i].split(VALS_SEP):
                try: 
                    [key, value] = [s.strip() for s in v.split('=',1)]

                    eventStr[mapIndexNonAtomic[fieldNames[i]]][key] = cast(value)
                except Exception as e:
                    print(f"Error processing dictionary attribute values: {e}", file=sys.stderr)
                    print(f"line {line+1}: {v}", file=sys.stderr)
        else:
            print("Wrong attribute format", file=sys.stderr)

    return eventStr
# ---------------------------------------
# setOfEvents: {a,b,c}
# Creates a function for each event and makes it global for execution

def create_and_make_public_atomic_functions(setOfEvents: Set[str]) -> None:
    for e in setOfEvents:  # a = MC.atom('a')
        globals()[e] = MC.atom(e)
# ---------------------------------------
# Returns the information about attributes in the header line
# From "aE,nV,@att,$p" it will return
# the tuple with (atribDesc, formats, fieldNames), three lists with, respectively,
# the description of each attribute, and the formats and names of each one
# (['aE','nV','@att','$p', ...],['a','n','@','$', ...],['E','V','att','p', ...])
def get_attrib_features(head: str) -> Tuple[List[str],List[str],List[str]]:
    atribDesc = head.split(ID_SEP)
    # a,n,@,$
    formats = tuple(f[0] for f in atribDesc)
    for f in formats:
        if not f in {'a', 'n', 'b', 's', '@', '$'}:
            print(f"Unknow attribute type: '{f}' in '{head}'. \nI cannot continue", file=sys.stderr)
            sys.exit()

    # E,V,att,p, ...
    # lets create global variables to access event colums by name, plus one for the 'atomics' 
    # For instance, if the attribute name is 'timestamp', in a DLTL formula code will be accessed
    # as in the example: 'F x.("(x) x[timestamp]>1000")'
    fieldNames = tuple(f[1:] for f in atribDesc)
    # non-atomic columns are applied to correlative positions in the tuple event (0 pos for atomics)
    for i in range(len(fieldNames)):
        if formats[i] != 'a':
            mapIndexNonAtomic[fieldNames[i]] = nextIndexNonAtomic()
            # define and export global variables with indexes of the columns
            # to which values correspond. Each one has as var name
            # the name of the column
            globals()[fieldNames[i]] = mapIndexNonAtomic[fieldNames[i]]
    return (atribDesc, formats, fieldNames)
# ---------------------------------------
# loads the log
# Returns a dictionary with the log information
# The structure is the one assigned by default to "logData"

def load_mod(pathRoot: str) -> logInfo:
    logData = {'nTraces': 0, 'nEvents': 0, 'atomics': set(),
               'traceLengths': dict(), 'sortedIDs': [],
               'traces': dict(), 'path': pathRoot,
               'attrib_desc': ""}

    with open(pathRoot + SUF_MOD, 'r') as f:
        head = f.readline().strip()
        # aE,nV,@att,$p, ...
        (atribDesc, formats, fieldNames) = get_attrib_features(head)
        nLine = FIRST_EVENT_INDEX
        # logData['traces'][id] is the trace
        for line in f:
            line = line.strip()
            # log[i]: id1,a&4&a;1&a=1;b=2
            parts = line.split(ID_SEP)
            id = parts[0]
            # valAtribs: [a, 4, "a;1", "a=1;b=2"]
            valsAtribs = parts[1].split(ATRIB_SEP)
            eventStruct = generate_event(formats, fieldNames, valsAtribs, nLine)
            # add the atomics
            logData['atomics'] = logData['atomics'] | eventStruct[I_ATOM]
            # the position of the first event is 1, no 0
            # for historic reasons
            if id in logData['traces']:
                eventStruct[I_POS] = len(logData['traces'][id]) + 1
                logData['traces'][id].append(tuple(eventStruct))
            else:
                eventStruct[I_POS] = 1
                logData['traces'][id] = [tuple(eventStruct)]
            nLine += 1

        create_and_make_public_atomic_functions(logData['atomics'])
        logData['attrib_desc'] = atribDesc
        logData['sortedIDs'] = sorted(logData['traces'])
        logData['nTraces'] = len(logData['traces'])
        for id in logData['sortedIDs']:
            logData['traceLengths'][id] = len(logData['traces'][id])
        
        for id in logData['sortedIDs']:
            logData['traces'][id] = tuple(logData['traces'][id])
            
        logData['nEvents'] = sum([len(logData['traces'][id])
                                 for id in logData['sortedIDs']])

    return logData

# ---------------------------------------
def print_info_log(logData: logInfo) -> None:
    print("----------------------------------------")
    print(f"file:      {logData['path']}.mod")
    print(f"#traces:   {logData['nTraces']}")
    print(f"#events:   {logData['nEvents']}")
    print(f"#atomics:  {len(logData['atomics'])}")
    print(f"att. desc: {logData['attrib_desc']}")
    print("----------------------------------------")
# ---------------------------------------
def save_trace_lengths(logData: logInfo) -> None:
    with open(logData['path'] + '_longs_trazas.csv', "w") as f:
        for id in logData['sortedIDs']:
            f.write(f"{id},{logData['traceLengths'][id]}\n")
# ---------------------------------------
# log_prefix.res: row id_trace,1,0,1..... (one column per evaluated formula)
# log_prefix.counts: as "res", but counting how many events verify satisfied the formula
# log_prefix.norm: the previous one, but normalized wrt the trace length
# log_prefix.forms: one line per checked formula, in order
def save_results(logData:logInfo, results: Dict[str, str], 
                 results_counts: Dict[str, str], checkedForms: List[str]) -> None:
    with open(logData['path'] + '.res', "w") as fR:
        with open(logData['path'] + '.norm', "w") as fC:
            for id in logData['sortedIDs']:
                fR.write(f"{results[id]}\n")
                fC.write(f"{results_counts[id]}\n")
    with open(logData['path'] + '.forms', "w") as fF:
        for f in checkedForms:
            fF.write(f"{f}\n")
# ---------------------------------------
# ids of traces whose answer was true (false)
# useful for exploring the log
# results[id] = "id,1,0,1,...

def who(logData: logInfo, results: Dict[str, str]) -> str:
    return what(logData, results, '1')

def who_not(logData: logInfo, results: Dict[str, str]) -> str:
    return what(logData, results, '0')

def what(logData: logInfo, results: Dict[str, str], val: str) -> str:
    listIds = ""
    for id in logData['sortedIDs']:
        if val == results[id].rpartition(',')[-1]: # everything after last ','
            listIds += id + " "
    return listIds
# ---------------------------------------
# Given a formula, possibly containing macros like '?activities', and
# a dictionary of the form {..., '?activities': ('load', 'mark', 'unload'), ...}
# generates a list of formulas, one for each possible value of '?activities'.
# If multiple macros are involved, formulas are generated for the Cartesian
# product of all of them.
# Warning: be careful with large sequences of linked replacements.

def unfold_macros(formula: str, macroDict: Dict[str, Tuple[str, ...]]) -> List[str]:
    queue = [formula]
    finalFormulas = []
    
    # Store all found strings
    visitedFormulas = {formula} 

    # In the case of cyclic macro definitions, we want to stop and warn
    MAX_ITERATIONS = 1000 
    iterations = 0

    while queue and iterations < MAX_ITERATIONS:
        currentString = queue.pop(0)
        iterations += 1
        
        foundKeys = [key for key in macroDict if key in currentString]

        if not foundKeys:
            finalFormulas.append(currentString)
        else:
            # replace longer keys first 
            foundKeys = sorted(foundKeys, key=len, reverse=True)
            keyToReplace = foundKeys[0]
            replacements = macroDict[keyToReplace]
            
            allNewFormulasVisited = True

            for replacementValue in replacements:
                newString = currentString.replace(keyToReplace, replacementValue)
                
                # new string generated. Maybe it is already in "visitedFormulas"
                # but, even in this case, it has to be considered
                visitedFormulas.add(newString)
                queue.append(newString)
                allNewFormulasVisited = False
    # If the loop terminated due to MAX_ITERATIONS, we might have partial results
    if iterations >= MAX_ITERATIONS:
        print(f"Warning: Reached max iterations ({MAX_ITERATIONS}). Possible unbounded expansion.", file=sys.stderr)

    return list(finalFormulas)
# ---------------------------------------
# pretty-print the log. Useless for big logs
def show(log: logInfo) -> None:
    pprint.pprint(log, indent=2, width=40)
# ---------------------------------------
if __name__ == "__main__":
    logData = load_mod("test/dos_trazas")
    print_info_log(logData)

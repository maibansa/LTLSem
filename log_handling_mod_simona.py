#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
---------------------------------------------------------------------------
File:   log_handling.py
Author: J. Ezpeleta
Date:   mayo-2025
Coms:   Invoke as
           python log_handling.py <fich_mod_sin_ext>

        File "<fich_mod_sin_ext>.mod" must the log model

        a,b,_End_
        aE,nV,@att,$p
        14
        id1,c
        id1,a&1&a;1&a=1;b=2
        id1,b&1&a;2&a=1;b=2
        ...

---------------------------------------------------------------------------
"""
import os
import sys
import DLTL as MC

import re
import itertools
import pprint

import csv, io

ID_SEP = ','
ATRIB_SEP = '&'
VALS_SEP = ';'

FIRST_EVENT_INDEX = 3 #lines 1-3 are atomics, header, number of events

# global variable to keep the IDs ordered, and use it when saving results
IDS = []

# Each column name, "name", not being of an atomic proposition will generate
# a variable with the name "name" whose value is the index in the event tuple corresponding
# to that column. This is so because all the atomic colums are stored in the first component
# of the tuple, while those that are not atomic will be stored in consecutive positions.
# For instace, if the colums are of types "a,n,a,a,s" and the column name are "n1,n2,n3,n4,n5",
# those with type "a" will go to position 0, while "n2" and "n5" will be at positions 1 and 2, resp.
# Therefore, mapIndexNonAtomic['n2'] = 2
mapIndexNonAtomic = dict()

# ---------------------------------------
# cast the string as either float, bool or string
def cast(value_str):
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
def to_valid_identifier(s):
    # Replace non-word chars with _
    s = re.sub(r'\W|^(?=\d)', '_', s)
    return s
# ---------------------------------------
# formats: (a,n,@,$)
# fieldNames: (E,V,att,p)
# valsAtribs: [a, 4, "a;1", "a=1;b=2"]
# line: line of the event
# devolverá el evento como una tupla
# ('atomics':set('a'), 4, set('a','1'), dict('a':1,'b':2))
SUF_GRAPH = "_g"
# ---------------------------------------
def generate_event(formats, fieldNames, valsAtribs, line):
    # create an empty event as a list, whose first el is the set for attributes in the event
    eventStr = [set()]
    for f in formats:
        if f == '@':  # a set of strings
            eventStr.append(set())
        elif f == '$':  # es un diccionario, k1=v1;k2=v2; ....
            eventStr.append(dict())
        elif f == 'a':  # an atomic, will be stored in eventStr[0], already created
            pass
        else: #place for scalar primitive types: int, bool, float, ....
            eventStr.append(None)

    return generate_event_simple_tuple(formats, fieldNames, valsAtribs, line, eventStr)

# ---------------------------------------
# the event is semantically correct wrt the log structure
# the structure to store the event information has been created when invoking,
# being eventStr[0] the set of atomics
def generate_event_simple_tuple(formats, fieldNames, valsAtribs, line, eventStr):
    # there will have as many elements as formats, plus 1 for atomics
    # Insert attribute values into the structure
    for i in range(len(formats)):
        if formats[i] == 'a':
            eventStr[0].add(valsAtribs[i]) #atomic proposition
        elif formats[i] in ('n', 's', 'b'):
            eventStr[mapIndexNonAtomic[fieldNames[i]]] = cast(valsAtribs[i])
        elif formats[i] == '@': #set
            for v in valsAtribs[i].split(VALS_SEP):
                eventStr[mapIndexNonAtomic[fieldNames[i]]].add(v.strip())
        elif formats[i] == '$': #dict
            for v in valsAtribs[i].split(VALS_SEP):
                try: 
                    # [key, value] = [s.strip() for s in v.split('=')]
                    [key, value] = [s.strip() for s in v.split('=',1)]

                    eventStr[mapIndexNonAtomic[fieldNames[i]]][key] = cast(value)
                except Exception as e:
                    print(f"Error processing dictionary attribute values: {e}", file=sys.stderr)
                    print(f"line {line+1}: {v}", file=sys.stderr)
        else:
            print("Formato de atributo incorrecto", file=sys.stderr)

    return tuple(eventStr)
# ---------------------------------------
# listOfEvents: "a,b,c"
# Creates a function for each event and makes it global for execution
def create_and_make_public_atomic_functions(listOfEvents):
    events = listOfEvents.split(ID_SEP)
    for e in events:  # a = MC.atom('a')
        exec(f"{e} = MC.atom('{e}')", globals())
# ---------------------------------------
# loads the log
# Returns a dictionary with the log information
# The structure is the one assigned by default to "logData"

def load_mod(pathRoot):
    # ---------------------------------------
    # index generator for columns with non-atomic values
    nextIndex = 0
    def nextIndexNonAtomic():
        nonlocal nextIndex
        nextIndex += 1
        return nextIndex
    # ---------------------------------------
    logData = {'nTraces': 0, 'nEvents': 0, 'atomics': set(),
               'traceLengths': dict(), 'sortedIDs': [],
               'traces': dict(), 'path': pathRoot,
               'attrib_desc': ""}

    with open(pathRoot + '.mod', 'r') as f:
        log = f.readlines()
    # eliminar saltos de línea
    log = list(map(str.strip, log))

    # each atomic variable will be a function
    create_and_make_public_atomic_functions(log[0])
    logData['atomics'] = set(log[0].split(ID_SEP))
    # aE,nV,@att,$p, ...
    atribDesc = log[1].split(ID_SEP)
    # a,n,@,$
    formats = tuple(f[0] for f in atribDesc)
    # E,V,att,p, ...
    # lets create global variables to access event colums by name, plus one for the 'atomics' 
    # For instance, if the attribute name is 'timestamp', in a DLTL formula code will be accessed
    # as in the example: 'F x.("(x) x[timestamp]>1000")'
    fieldNames = tuple(f[1:] for f in atribDesc)
    # non-atomic columns are applied to correlative positions in the tuple event (0 pos for atomics)
    for i in range(len(fieldNames)):
        if formats[i] != 'a':
            mapIndexNonAtomic[fieldNames[i]] = nextIndexNonAtomic()
            globals()[fieldNames[i]] = mapIndexNonAtomic[fieldNames[i]]

    # logData['traces'][id] será la traza de id
    for i in range(FIRST_EVENT_INDEX, len(log)):
        # log[i]: id1,a&4&a;1&a=1;b=2
        parts = log[i].split(ID_SEP)
        id = parts[0]
        # valAtribs: [a, 4, "a;1", "a=1;b=2"]
        valsAtribs = parts[1].split(ATRIB_SEP)
        eventStruct = generate_event(formats, fieldNames, valsAtribs, i)
        if id in logData['traces']:
            logData['traces'][id].append(eventStruct)
        else:
            logData['traces'][id] = [eventStruct]

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

def print_info_log(logData):
    print("----------------------------------------")
    print(f"file:      {logData['path']}.mod")
    print(f"#traces:   {logData['nTraces']}")
    print(f"#events:   {logData['nEvents']}")
    print(f"#atomics:  {len(logData['atomics'])}")
    print(f"att. desc: {logData['attrib_desc']}")
    print("----------------------------------------")
# ---------------------------------------
def save_trace_lengths(logData):
    with open(logData['path'] + '_longs_trazas.txt', "w") as f:
        for id in logData['sortedIDs']:
            f.write(f"{id},{logData['traceLengths'][id]}\n")

def save_results(logData, results, results_counts, checkedForms):
    with open(logData['path'] + '.res', "w") as fR:
        with open(logData['path'] + '.norm', "w") as fC:
            for id in logData['sortedIDs']:
                fR.write(f"{results[id]}\n")
                fC.write(f"{results_counts[id]}\n")
    with open(logData['path'] + '.forms', "w") as fF:
        for f in checkedForms:
            fF.write(f"{f}\n")

# results[id] = "id,1,0,1,...
def who(logData, results):
    return what(logData, results, '1')


def who_not(logData, results):
    return what(logData, results, '0')

def what(logData, results, val):
    listIds = ""
    for id in logData['sortedIDs']:
        res = results[id].rpartition(',')[-1]  # todo de después de última ','
        if res == val:
            listIds += id + " "
    return listIds
# ---------------------------------------
# Given a formula, possibly containing macros like '?activities', and
# a dictionary of the form {..., '?activities': ('load', 'mark', 'unload'), ...}
# generates a list of formulas, one for each possible value of '?activities'.
# If multiple dictionaries are involved, formulas are generated for the Cartesian
# product of all dictionaries.
# Warning: be careful with large dictionaries.

def unfold_macros(formulaWithMacros, dictMacros):
    # Find all macros that appear in the formula
    keysInString = [key for key in dictMacros if key in formulaWithMacros]
    formulas = [formulaWithMacros]

    # Sort by length descending to replace longer macros first
    keysInString.sort(key=len, reverse=True)

    if not keysInString:
        return formulas  # no macros

    for macro in keysInString:
        newFormulas = []
        #print(f"macro: {macro}")
        for f in formulas:
            # Ensure dictMacros[macro] is always iterable
            values = dictMacros[macro]
            if isinstance(values, str):
                values = [values]  # wrap single string in list

            # Replace macro with each value
            for v in values:
                #print(f"v: {v}")
                if (v == "") or (v[0] != '(' and v[-1] != ')'):
                    # print(f"{v[0]}:{v}:{v[-1]} es string")
                    v = f"'{v}'"

                newFormulas += [f.replace(macro, v)]

        formulas = newFormulas
    return formulas
# ---------------------------------------
def show(log):
    pprint.pprint(log, indent=2, width=40)
# ---------------------------------------
if __name__ == "__main__":
    logData = load_mod_new("test/dos_trazas")
    print_info_log_new(logData)

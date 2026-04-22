"""
------------------------------------------------------------------
File:   DLTL.py
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

import re
import copy

# user defined propositions that can be used in lambda-like 
# expressions in formulas
import my_propositions as PROP

import sys
import traceback

import importlib

#-----------------------------------
# When loading the log, each input column will be associated to the index in the tuple
# representing each event, with all the colums of type "atomic" associated to pos 0.
# For instance, if there is a colum "timestamp", whose position in the tuple-event is 3
# log_handling will create a variable named "timestamp" with value 3. We need to import
# that variables. They will be used in the execution of "eval" in function "replace"
from collections import ChainMap
import log_handling
eval_env = ChainMap(locals(), log_handling.__dict__)
#-----------------------------------

"""
A expression can be:
[{...}, 'True']          #{...}: if not empty, it is the list of freezy variables in the exp
[{...}, 'False']
[{...}, 'atom', 'z']      #'z' represents a proposition
[{...}, '!', exp]
[{...}, 'F', exp]
[{...}, 'O', exp]
[{...}, 'X', exp]
[{...}, 'Y', exp]
[{...}, 'G', exp]
[{...}, 'H', exp]
[{...}, '&', exp1, exp2]
[{...}, '|', exp1, exp2] 
[{...}, 'U', exp1, exp2]
[{...}, 'S', exp1, exp2]
[{...}, 'fvar', 'z', exp]   
[{...}, 'exp', exp]
    * The third element is a string containing any expression
    * that can be evaluated in the context of the trace.
    * An example: "(x,y)x[t]+y[t] > 3+PROP.f(7)"
    * where x and y are the variables the expression depends on,
    * and PROP.f(7) is a function defined in the `funcs` module.
    * Any function evaluable in the current context can be used.

IMPORTANT:
    ONLY NUMERIC FIELDS CAN BE USED IN NUMERIC OPERATIONS. 

    For example: you can write an expression like "(x)x[V] > 1"  
    if the attribute has been declared as type 'n' (which is stored as a `double`).  
    You could also write "x[p]['b'] == 2" if p is a dictionary-type and
    if x[p]['b'] is of a numeric type
"""

THE_TRACE = []  # current trace
# ---------------------------------------
# var set, type of formula and expressions indexes
v, t, e1, e2 = 0, 1, 2, 3
I_ATOM = 1 #index 1 of an event will store the set of atomics in the event
# ---------------------------------------
TRUE_VAL = [set(), 'True']
FALSE_VAL = [set(), 'False']
# ---------------------------------------
# MC.py can dynamically load functions and vars executing the "_LOAD" command
# For these elements be used in the queries, the must be incorporated to the
# globals of DLTL. This
# newM: a module, created by MC.py (see "case_load" function)
def importNewModule(modName, newM):
    globals()[modName] = newM
# ---------------------------------------
def is_false(exp):
    return (len(exp[v]) == 0) and (exp[t] == 'False')

def is_true(exp):
    return (len(exp[v]) == 0) and (exp[t] == 'True')
# ---------------------------------------
# replace x[...] in THE_TRACE
def replace(i, exp, var):
    stack = [(exp, False)]
    resultMap = {}

    while stack:
        theForm, visited = stack.pop()

        if id(theForm) in resultMap:
            continue

        vars = theForm[v]
        op = theForm[t]

        if var not in vars or is_false(theForm) or is_true(theForm):
            resultMap[id(theForm)] = theForm
            continue

        if visited: #descendent results must be in the stack
            if op in {'atom', '!', 'X', 'G', 'F', 'Y', 'H', 'O'}:
                newExp1 = resultMap[id(theForm[e1])]
                resultMap[id(theForm)] = [vars - {var}, op, newExp1]
            elif op in {'&', '|', 'U', 'S'}:
                newExp1 = resultMap[id(theForm[e1])]
                newExp2 = resultMap[id(theForm[e2])]
                resultMap[id(theForm)] = [vars - {var}, op, newExp1, newExp2]
            elif op == 'fvar':
                newExp1 = resultMap[id(theForm[e2])]
                resultMap[id(theForm)] = [
                    vars - {var}, op, theForm[e1], newExp1]
            elif op == 'exp':
                formula = theForm[e1]
                if isinstance(formula, str):
                    newFormula = formula.replace(f"{var}[#]", str(i+1)) #first event positions is 1, not 0. Historical reasons
                    pattern = rf'\b{re.escape(var)}\b'
                    newFormula = re.sub(pattern, f"THE_TRACE[{i}]", newFormula)
                    newVars = vars - {var}
                    if len(newVars) == 0:
                        resultMap[id(theForm)] = [
                            newVars, str(eval(newFormula, {}, eval_env))]
                    else:
                        resultMap[id(theForm)] = [newVars, op, newFormula]
                else:
                    print('*** I SHOULD NOT BE HERE!!')
                    resultMap[id(theForm)] = theForm
        else:
            # postorder: reinsert with visited=True and process descendents
            stack.append((theForm, True))
            # descendientes a la pila, pendientes de procesar
            if op in {'atom', '!', 'X', 'G', 'F', 'Y', 'H', 'O'}:
                stack.append((theForm[e1], False))
            elif op in {'&', '|', 'U', 'S'}:
                stack.append((theForm[e1], False))
                stack.append((theForm[e2], False))
            elif op == 'fvar':
                stack.append((theForm[e2], False))
            # elif op == 'exp':
            #     # nada que hacer
            #     pass

    return resultMap[id(exp)]
# ---------------------------------------
def eval_formula_in_event(exp, i, traza):
    # (exp, False): children not yet processed  
    # (exp, True): children already resolved and their value stored in resultMap
    stack = [(exp, False)]
    # Expressions already evaluated, indexed by their id
    resultMap = {}

    while stack:
        theForm, visited = stack.pop()

        # already done
        if id(theForm) in resultMap:
            continue

        vars = theForm[v]
        op = theForm[t]

        # true or false, or non-evaluable because of the vars
        if len(vars) != 0 or is_false(theForm) or is_true(theForm):
            resultMap[id(theForm)] = theForm
            continue

        if visited:
            # children must be on the stack and processed
            if op == 'exp':
                val = theForm[e1]
                try:
                    val_str = str(eval(val)) if isinstance(
                        val, str) else str(eval(str(val)))
                except Exception as ex:
                    print(f"Eval error in 'exp': {ex}")
                    val_str = "False"
                resultMap[id(theForm)] = [set(), val_str]
            elif op == 'atom':
                atom_val = theForm[e1]
                resultMap[id(theForm)] = \
                    TRUE() if atom_val in traza[i][v] else FALSE() #set of atoms in pos 0 of the even tuple
                    # TRUE() if atom_val in traza[i]['atomics'] else FALSE()
            elif op == '&':
                ev1 = resultMap[id(theForm[e1])]
                ev2 = resultMap[id(theForm[e2])]
                if is_false(ev1) or is_false(ev2):
                    resultMap[id(theForm)] = FALSE()
                elif is_true(ev1) and is_true(ev2):
                    resultMap[id(theForm)] = TRUE()
                elif is_true(ev1):
                    resultMap[id(theForm)] = ev2
                elif is_true(ev2):
                    resultMap[id(theForm)] = ev1
                else:
                    resultMap[id(theForm)] = [ev1[v] | ev2[v], '&', ev1, ev2]
            elif op == '|':
                ev1 = resultMap[id(theForm[e1])]
                ev2 = resultMap[id(theForm[e2])]
                if is_true(ev1) or is_true(ev2):
                    resultMap[id(theForm)] = TRUE()
                elif is_false(ev1):
                    resultMap[id(theForm)] = ev2
                elif is_false(ev2):
                    resultMap[id(theForm)] = ev1
                else:
                    resultMap[id(theForm)] = [ev1[v] | ev2[v], '|', ev1, ev2]
            elif op == '!':
                ev = resultMap[id(theForm[e1])]
                if len(ev[v]) == 0:
                    resultMap[id(theForm)] = FALSE(
                    ) if ev[t] == 'True' else TRUE()
                else:
                    resultMap[id(theForm)] = [ev[v], '!', ev]
            elif op == 'fvar':
                new_exp = replace(i, theForm[e2], theForm[e1])
                stack.append((new_exp, False))
                # Aún no se puede resolver
                stack.append((theForm, True))
        else:
            stack.append((theForm, True))
            # preorder: descendents first
            if op in {'&', '|'}:
                stack.append((theForm[e2], False))
                stack.append((theForm[e1], False))
            elif op == '!':
                stack.append((theForm[e1], False))

    return resultMap[id(exp)]
# ---------------------------------------
def eval_X(exp, traza):
    vars, op, n = exp[v], exp[t], len(traza)
    res = [None] * n

    if is_false(exp[e1]):
        res[n-1] = TRUE()
    else:
        res[n-1] = FALSE()

    eval_exp = eval_formula(exp[e1], traza)
    for i in reversed(range(n-1)):
        res[i] = eval_exp[i+1]
    return res

def eval_Xn(exp, traza):
    # print(f"eval_Xn: {exp}")
    return eval_formula(exp, traza)

def eval_U(exp, traza):
    vars, op, n = exp[v], exp[t], len(traza)
    res = [None] * n
    f = exp[e1]
    g = exp[e2]

    res_f = eval_formula(f, traza)
    res_g = eval_formula(g, traza)
    res[n-1] = res_g[n-1]
    for i in reversed(range(n-1)):
        res[i] = eval_formula_in_event(
            OR(res_g[i], AND(res_f[i], res[i+1])), i, traza)
    return res

def eval_F(exp, traza):
    vars, op, n = exp[v], exp[t], len(traza)
    res = [None] * n
    f = exp[e1]

    res_parcial = eval_formula(f, traza)

    res[n-1] = eval_formula_in_event(res_parcial[n-1], n-1, traza)
    for i in reversed(range(n-1)):
        res[i] = eval_formula_in_event(OR(res_parcial[i], res[i+1]), i, traza)
    return res

def eval_Fn(exp, traza):
    # print(f"eval_Fn: {exp}")
    return eval_formula(exp, traza)

def eval_G(exp, traza):
    vars, op, n = exp[v], exp[t], len(traza)
    res = [None] * n
    f = exp[e1]
    res_parcial = eval_formula(f, traza)

    res[n-1] = eval_formula_in_event(res_parcial[n-1], n-1, traza)
    for i in reversed(range(n-1)):
        res[i] = eval_formula_in_event(AND(res_parcial[i], res[i+1]), i, traza)
    return res
# ---------------------------------------
def eval_Y(exp, traza):
    n = len(traza)
    res = [None] * n

    if is_false(exp[e1]):
        res[v] = TRUE()
    else:
        res[v] = FALSE()

    res_exp = eval_formula(exp[e1], traza)
    for i in range(1, n):
        res[i] = res_exp[i - 1]

    return res

def eval_Yn(exp, traza):
    return eval_formula(exp, traza)

def eval_S(exp, traza):
    n = len(traza)
    res = [None] * n
    f = exp[e1]
    g = exp[e2]

    res_f = eval_formula(f, traza)
    res_g = eval_formula(g, traza)

    res[v] = res_g[v]
    for i in range(1, n):
        res[i] = eval_formula_in_event(
            OR(res_g[i], AND(res_f[i], res[i-1])), i, traza)
    return res

def eval_O(exp, traza):
    n = len(traza)
    res = [None] * n
    f = exp[e1]

    res_f = eval_formula(f, traza)
    res[v] = eval_formula_in_event(res_f[v], 0, traza)
    for i in range(1, n):
        res[i] = eval_formula_in_event(OR(res_f[i], res[i - 1]), i, traza)
    return res

def eval_On(exp, traza):
    # print(f"eval_On: {exp}")
    return eval_formula(exp, traza)

def eval_H(exp, traza):
    n = len(traza)
    res = [None] * n
    f = exp[e1]

    res_f = eval_formula(f, traza)
    res[v] = eval_formula_in_event(res_f[v], 0, traza)
    for i in range(1, n):
        res[i] = eval_formula_in_event(AND(res_f[i], res[i - 1]), i, traza)
    return res
# ---------------------------------------
def eval_True_False(exp, traza):
    vars, op, n = exp[v], exp[t], len(traza)
    res = [None] * n
    for i in range(n):
        res[i] = [set(), exp[t]]
    return res

def eval_Not(exp, traza):
    vars, op, n = exp[v], exp[t], len(traza)
    res = [None] * n

    res_f = eval_formula(exp[e1], traza)

    res = [eval_formula_in_event(NOT(res_f[i]), i, traza) for i in range(n)]
    return res

def eval_AND(exp, traza):
    vars, op, n = exp[v], exp[t], len(traza)
    res = [None] * n

    res_f1 = eval_formula(exp[e1], traza)
    res_f2 = eval_formula(exp[e2], traza)

    for i in range(n):
        ev1 = res_f1[i]
        ev2 = res_f2[i]
        res[i] = eval_formula_in_event(
            [ev1[v] | ev2[v], '&', ev1, ev2], i, traza)
    return res

def eval_OR(exp, traza):
    vars, op, n = exp[v], exp[t], len(traza)
    res = [None] * n

    res_f1 = eval_formula(exp[e1], traza)
    res_f2 = eval_formula(exp[e2], traza)

    for i in range(n):
        ev1 = res_f1[i]
        ev2 = res_f2[i]
        res[i] = eval_formula_in_event(
            [ev1[v] | ev2[v], '|', ev1, ev2], i, traza)
    return res

def eval_fvar(exp, traza):
    vars, op, n = exp[v], exp[t], len(traza)
    freezeVar = exp[e1]
    newRow = eval_formula(exp[e2], traza)
    newRow = [replace(i, newRow[i], freezeVar) for i in range(n)]
    newRow = [eval_formula_in_event(newRow[i], i, traza) for i in range(n)]
    return newRow

def eval_exp(exp, traza):
    return [eval_formula_in_event(exp, i, traza) for i in range(len(traza))]

# The set of atomic vars are in "event[I_ATOM]"
def eval_atom(exp, traza):
    return [TRUE() if exp[e1] in event[I_ATOM] else FALSE() for event in traza]

def eval_formula(exp, traza=None):
    cases = {
        'X': eval_X,
        'Xn': eval_Xn,
        'U': eval_U,
        'F': eval_F,
        'Fn': eval_Fn,
        'G': eval_G,
        'Y': eval_Y,
        'Yn': eval_Yn,
        'S': eval_S,
        'H': eval_H,
        'O': eval_O,
        'On': eval_On,
        'True': eval_True_False,
        'False': eval_True_False,
        '!': eval_Not,
        '&': eval_AND,
        '|': eval_OR,
        'fvar': eval_fvar,
        'exp': eval_exp,
        'atom': eval_atom
    }
    try:
        global THE_TRACE
        THE_TRACE = traza
        res = cases[exp[t]](exp, traza)
        return res
    except Exception as e:
        print(f"An error occurred: {e}", file=sys.stderr)
        print("\n--- Full Traceback ---", file=sys.stderr)
        traceback.print_exc(file=sys.stdout)
        print("returning FALSE value\n", file=sys.stderr)
        print("----------------------\n", file=sys.stderr)
        return FALSE_VAL
# ---------------------------------------
def TRUE():
    return TRUE_VAL.copy()

def FALSE():
    return FALSE_VAL.copy()

def atom(var):
    return [set(), 'atom', var]

def expression(vars, expression_string):
    return [vars, 'exp', expression_string]

def fvar(var, expression):
    return [{var}.union(expression[v]), 'fvar', var, expression]

def AND(exp1, exp2):
    return [exp1[v] | exp2[v], '&', exp1, exp2]

def OR(exp1, exp2):
    return [exp1[v] | exp2[v], '|', exp1, exp2]

def NOT(exp):
    return [exp[v], '!', exp]

def X(exp):
    return [exp[v], 'X', exp]

def Xn(n, exp):
    n = int(n)
    newExp = [exp[v], 'X', exp]
    for i in range(n-1):
        newExp = [exp[v], 'X', newExp]
    return newExp

def U(exp1, exp2):
    return [exp1[v] | exp2[v], 'U', exp1, exp2]

def G(exp):
    return [exp[v], 'G', exp]
# ---------------------------------------
def F(exp):
    return [exp[v], 'F', exp]

def Fn(n, exp):
    n = int(n)
    if n == 1:
        return [exp[v], 'F', exp]
    else:
        return AND(exp, [exp[v], 'X', Fn(n-1, exp)])

def Y(exp):
    return [exp[v], 'Y', exp]

def Yn(n, exp):
    n = int(n)
    newExp = [exp[v], 'Y', exp]
    for i in range(n-1):
        newExp = [exp[v], 'Y', newExp]
    return newExp

def S(exp1, exp2):
    return [exp1[v] | exp2[v], 'S', exp1, exp2]

def O(exp):
    return [exp[v], 'O', exp]

def On(n, exp):
    n = int(n)
    if n == 1:
        return [exp[v], 'O', exp]
    else:
        return AND(exp, [exp[v], 'Y', On(n-1, exp)])

def H(exp):
    return [exp[v], 'H', exp]

def IMP(exp1, exp2):
    return OR(exp2, NOT(exp1))

def EQ(exp1, exp2):
    return AND(IMP(exp1, exp2), IMP(exp2, exp1))
# ---------------------------------------
# Given the results of a formula evaluation, returns:
# * whether it holds at the first event (classic model checker result)
# * number of true evaluations
# * average of true evaluations
def results_statistics(res):
    n = len(res)
    trueCount = 0
    falseCount = 0
    for i in range(n):
        if is_true(res[i]):
            trueCount += 1
        elif is_false(res[i]):
            falseCount += 1

    if trueCount + falseCount != n:
        print(f"*** ERROR: {trueCount + falseCount} != {n}")
        return None, None, None, None

    return (1 if is_true(res[0]) else 0), trueCount, falseCount, trueCount/n

def show_statistics(data):
    (tOf, trueCount, falseCount, media) = data
    print(f"\t{tOf},{trueCount},{falseCount},{media}")
# ---------------------------------------
def is_evaluable(formula):
    return len(formula[v]) == 0
# ---------------------------------------
# extended: extended format, shows the entire trace
# otherwise, only the first and last elements
# show("mens", [formula, time], extended)
def show(mess, resCheck, extended):
    res = resCheck[0]
    t = resCheck[1]
    if extended:
        cont = str(res)
    else:
        cont = str(res[0]) + ' ... ' + str(res[len(res) - 1])

    print(f"\n{mess}:\n{cont}\n{t}")
# ---------------------------------------

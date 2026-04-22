#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
---------------------------------------------------------------------------
File:   mod2new_mod.py
Author: J. Ezpeleta
Date:   febrero-2024
Coms:   invocar como 
           python mod2new_mod.py <fich_mod_sin_ext>
        
        El fichero "<fich_mod_sin_ext>.mod" tiene un modelo en el formato clásico de MC
		Genera "<fich_mod_sin_ext>.des" y "<fich_mod_sin_ext>.nmod" con:
		* la descripción de log, con las 3 primeras líneas de "<fich_mod_sin_ext>.mod"
		* "<fich_mod_sin_ext>.nmod", que contendrá una línea por traza, siendo el primer campo
		  el id de traza y el resto los eventos, separados por ","

		  	SI,ev_CRP&135343080
			SI,ev_CRP&135504000
			VHA,ev_ER_Registration&128970000
			VHA,ev_ER_Triage&128970578
		 será 
			SI,ev_CRP&135343080,ev_CRP&135504000
			VHA,ev_ER_Registration&128970000,ev_ER_Triage&128970578
---------------------------------------------------------------------------
"""
import os
import sys
import random

ATRIB_SEP = ','
# ---------------------------------------------------------------------------
# Cargará "path_root.mod" y generará "path_root.des" y "path_root.nmod"


def load_mod(path_root):

    with open(path_root + '.mod', 'r') as f:
        log = f.readlines()
    log = list(map(str.strip, log))
    return log
# ---------------------------------------------------------------------------


def generate_desc(log, path_root):
    with open(path_root + '.desc', 'w') as f:
        for i in range(3):
            f.write(log[i] + '\n')
# ---------------------------------------------------------------------------


def generate_nmod(log, path_root):
    traces = {}
    for e in log[3:]:
        trozos = e.split(ATRIB_SEP)
        id = trozos[0]
        event = trozos[1]
        if id in traces:
            traces[id].append(event)
        else:
            traces[id] = [event]

    with open(path_root + '.nmod', 'w') as f:
        for id in traces.keys():
            line = id
            for e in traces[id]:
                line += ATRIB_SEP + e
            f.write(line + '\n')
# ---------------------------------------------------------------------------


def log2new_mod():
    if len(sys.argv) < 1:
        print('uso: ' + sys.argv[0] + ' <fich_mod_sin_ext>')
        sys.exit(1)

    logSinExt = sys.argv[1]
    log = load_mod(logSinExt)
    generate_nmod(log, logSinExt)
# ---------------------------------------------------------------------------


def main_1():
    log = load_mod('log_sepsis')
    generate_nmod(log, 'log_sepsis')


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    if sys.argv != None and len(sys.argv) < 2:
        print('uso: ' + sys.argv[0] + ' <fich_nmod_sin_ext>')
        sys.exit(1)

    logSinExt = sys.argv[1]
    log = load_mod(logSinExt)
    generate_nmod(log, logSinExt)
    generate_desc(log, logSinExt)

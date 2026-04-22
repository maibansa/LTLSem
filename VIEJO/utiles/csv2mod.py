#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
---------------------------------------------------------------------------
File:   csv2mod.py
Author: J. Ezpeleta
Date:   diciembre-2024
Coms:   
  CaseID,Activity,Timestamp,Actor,ActionType,ModelReference,Details
  Case_1,Start,1751565600.0,User,Start,https://ontologia.segittur.es/turismo/def/core/Inicio,estur:activityType=Initialization;estur:actorType=Traveler
  Case_1,Validate user access,1751565660.0,System,Authentication,https://ontologia.segittur.es/turismo/def/core/Autenticacion,estur:authMethod=OAuth2;estur:accessLevel=User
  Case_1,Search flights,1751565720.0,User,Query,https://ontologia.segittur.es/turismo/def/core/BuscarVuelos,estur:searchType=Flight;estur:searchChannel=Web
  ...


---------------------------------------------------------------------------
"""
import os
import sys
import random

import pandas as pd

ATRIB_SEP = ','
cabeceraMod = "aActivity,nTimestamp,aActor,aActionType,sModelReference,$Details"
# ---------------------------------------------------------------------------
# process_id,api_name,timestamp,arguments,return_value


def load_log(path_root):
    log = pd.read_csv(path_root + '.csv')
    # eliminar " " de atributos
    log['Activity'] = log['Activity'].replace(r'[ -/]', '_', regex=True)
    log['Activity'] = "ac_" + log['Activity']

    log['Actor'] = log['Actor'].str.replace(r'[ -/]', '_', regex=True)
    log['ActionType'] = log['ActionType'].replace(r'[ -/]', '_', regex=True)
    log['ActionType'] = "at_" + log['ActionType']

    log.to_csv(path_root + '_cleaned.csv', index=False)

    events = set(log['Activity']) | set(log['Actor']) | set(log['ActionType'])
    return log, events
# ---------------------------------------------------------------------------


def generate_des(log, path_root):
    with open(path_root + '.desc', 'w') as f:
        for i in range(3):
            f.write(log[i] + '\n')
# ---------------------------------------------------------------------------


def generate_mod(log, events, path_root):
    lEvents = list(events)
    with open(path_root + '.mod', 'w') as f:
        lEvS = ','.join(lEvents)
        f.write(lEvS + '\n')

        f.write(cabeceraMod + '\n')
        f.write('999999' + '\n')

        for index, row in log.iloc[0:].iterrows():
            rowS = '&'.join(log.iloc[index, 1:].astype(str))
            rowS = log.iloc[index, 0] + ',' + rowS
            f.write(rowS + '\n')
# ---------------------------------------------------------------------------


def main_1():
    fichLogSinExt = '../semantic_logs/WFSemTrazas'
    log, events = load_log(fichLogSinExt)
    generate_mod(log, events, fichLogSinExt)


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    main_1()

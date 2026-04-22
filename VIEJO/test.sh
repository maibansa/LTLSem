#!/bin/bash


MC_HOME="../bin"
MODEL_CHECKER="${MC_HOME}/DLTL_lua"
WHERE_AM_I="$(pwd)"

LUA_SRC="${MC_HOME}/UP.lua"
LUA_ATS=""

MODEL="${WHERE_AM_I}/dos_trazas.mod"

#de momento desconozco fecha mínima concreta; lo genero poniendo la fecha cero=2000-08-02T02:17:45+0000
INIT="${WHERE_AM_I}/init.txt"

# "cd ${MC_HOME}"

"${MODEL_CHECKER}" "${MODEL}" -lua_pars "${LUA_SRC};${LUA_ATS}" -init "${INIT}" \
                                    -results results_new.txt -interactive

# "${MODEL_CHECKER}" "${MODEL}" -lua_pars "${LUA_SRC};${LUA_ATS}" -init "${INIT}" \
#                                     -results results_new.txt -server_short 2000

# cd "${WHERE_AM_I}"
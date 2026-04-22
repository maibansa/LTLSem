
import log_handling
import re

# ---------------------------------------
def quote(s):
    return '"' + s + '"'
# ---------------------------------------
#x.("(x)PROP.IN_DIC(x[p],'b',3)")
def IN_DIC(dicc, k, v):
    if k in dicc:
        return dicc[k] == v
    else:
        return False


#x.("(x)PROP.IN_DIC_2(x,p,'b',22)")
def IN_DIC_2(event, posDir, k, v):
    if k in event[posDir]:
        return event[posDir][k] == v
    else:
        return False
# ---------------------------------------
# -- LOGs de Apache
def diff_pos(x,y,diff):
    return y['#'] == x['#'] + diff

# ---------------------------------------
#  For the platoon example
#  check for a real value

def has_f_value(x, attrib, value):
    epsilon = 10e-6
    return -1.0e-6 <= math.abs(x[attrib],value) and  math.abs(x[attrib],value) <= -10e-6


# Are distances shorter than 'dist'?
# Pre: position of x in trace <= position of y in trace
def near(x, y, dist):
    return y[time] - x[time] <= 1.0e-6  and (abs(y[pos] - x[pos]) <= dist)


# F x.(id_0 & F y.(id_1 & "(x,y) near(x,y,12)"))
# F x.(id_1 & F y.(id_2 & "(x,y) near(x,y,11)"))
# F x.(id_1 & F y.(id_2 & "(x,y) PROP.near(x,y,11)"))


import re

# the two following values are defined in log_handling.py. They should
# be exported. TODO
I_POS = 0  #index in an event structure where the even pos in the trace is stored
I_ATOM = 1 #index in an event structure where the set of atoms is stored

def SAME_KEY_VALUE(dic1, dic2, k):

    if k in dic1 and k in dic2:
        return dic1[k] == dic2[k]
    else:
        return False
# ---------------------------------------
# attrib: attribute name
# pattern: r.e. to be checked against the att contents
#x.("(x)PROP.check_pattern(x[p],'b')")
def check_patt(attContent,pattern):
    return bool(re.search(pattern, attContent))

def check_patt_f(pattern):
    pattern = re.compile(pattern)
    return lambda x: bool(pattern.search(x))


def diff_att_geq(x, y, value):
    return y - x >= value
# --------------------------------------------------------------------
# -- LOGs de Apache
def diff_pos(x,y,diff):
    return y[I_POS] == x[I_POS] + diff

# --------------------------------------------------------------------
#  For the platoon example
#  check for a real value

def has_f_value(x, attrib, value):
    epsilon = 10e-6
    return -1.0e-6 <= math.abs(x[attrib],value) and  math.abs(x[attrib],value) <= -10e-6


# Are distances shorter than 'dist'?
# Pre: position of x in trace <= position of y in trace
def near(x, y, dist):
    return y[time] - x[time] <= 1.0e-6  and (abs(y[pos] - x[pos]) <= dist)


# F x.(id_0 & F y.(id_1 & "(x,y) near(x,y,12)"))
# F x.(id_1 & F y.(id_2 & "(x,y) near(x,y,12)"))
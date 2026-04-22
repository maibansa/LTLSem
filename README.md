================================================================================
MODEL CHECKER (MC.py) README
================================================================================

INTRODUCTION
--------------------------------------------------------------------------------
This file describes the use of a model checker for DLTL (Data-aware Linear
Temporal Logic) model checker.

REFERENCE:
The theoretical foundations are described in the following paper:

J. M. Couvreur, J. Ezpeleta
A Linear Temporal Logic Model Checking Method over Finite Words with Correlated
Transition Attributes
Proceedings of the 7th International Symposium on Data-driven Process Discovery
and Analysis (SIMPDA 2017), Neuchâtel, Switzerland, December 6-8, 2017,
ISSN: 1613-0073, Lecture Notes in Business Information Processing, Vol. 340,
Springer, Paolo Ceravolo, Maurice van Keulen and Kilian Stoffel (Eds.), 2019

================================================================================
USAGE
================================================================================

INVOCATION:
    python MC.py [parameters]

PARAMETERS:
    - If no parameters are provided, a help message is shown.
    - Parameters must be provided as key=value pairs, separated by spaces.

    ---------------------------------
    REQUIRED:
    ---------------------------------
    log-file=<filename>         The name of the log file (without the .mod suffix).
                                Example: log-file=system_trace

    ---------------------------------
    OPTIONAL:
    ---------------------------------
    multi-line=<true|false>     Allows formulas to span multiple lines. Formulas must
                                be terminated with a $ character.
                                (Default: false)

    interactive=<true|false>    Starts the model checker in interactive mode.
                                (Default: true)

    init-file=<path>            Path to a file containing initial setup commands.
                                Must include the file suffix/extension.
                                (Default: "")

    formula-file=<path>         Path to a file containing DLTL formulas to check.
                                Must include the file suffix/extension.
                                (Default: "")

================================================================================
INPUT FILE FORMAT (<filename>.mod)
================================================================================

The log file must follow a strict comma-separated format:

STRUCTURE:
    Line 1:   Attribute Headers List (defines columns and types)
    Line 2-:  Log Events (one event per line)

1. ATTRIBUTE HEADERS (Line 1)
------------------------------
The first character indicates the data type, followed by the attribute name:

    'a': The attribute is an atomic proposition.
    's': The attribute is a string.
    'n': The attribute is a number (treated as a float).
    'b': The attribute is a boolean.
    '@': The attribute is a set of strings (e.g., item1;item2).
    '$': The attribute is a dictionary of "key=value" pairs (e.g., name=John;age=34).

Note on Missing Values:
    - Numeric attributes default to 0.
    - Boolean attributes default to False.
    - String attributes default to '' (empty string).

2. LOG EVENTS (Line 2-)
-------------------------
Format: trace_id,event_name&attribute_1&attribute_2&attribute_3...

MODEL EXAMPLE:
    aE,nV,@att,$p
    id0,a&4&a;1&a=1;b=2
    id0,a&1&a;1&a=1;b=3
    id1,a&4&a;1&a=1;b=5
    id1,a&1&a;1&a=1;b=2
    id1,b&1&h;2&a=1;b=2
    id1,a&1&a;3&a=1;b=2
    id1,a&1&a;4&a=1;b=7
    id1,b&1&a;1&a=1;b=1
    id2,b&2&a;2&a=3;b=3
    id2,b&2&234;3;j&a=1;b=2

================================================================================
FORMULA SYNTAX AND OPERATORS
================================================================================

PROPOSITIONS:
    - Any atomic proposition. These correspond to the values appearing
      in colums of type attribute
    - Any function returning a boolean and involving event attributes.
      These functions (non-atomic propositions) must be written in a lambda-definition style, with Python syntax. This will be shown later on.

---------------------------------
LOGIC OPERATORS
---------------------------------
    ! f     NOT f
    f | g   f OR g
    f & g   f AND g
    f -> g  If f then g
    f <-> g f if and only if g

---------------------------------
LTL OPERATORS
---------------------------------
    G f     Always 'f' (Globally, future)
    H f     'f' happens for every past state (Historical Always)
    F f     Eventually 'f' will happen (Future)
    O f     'f' happened in the past (Once)
    X f     'f' happens at the Next event (False for the last event)
    Y f     'f' happened at the previous event (False for the first event)
    f U g   'f' happens Until 'g' is met
    f S g   'g' happens Since 'f' happened

Note: Parentheses can be used for grouping expressions.

---------------------------------
FREEZE OPERATOR
---------------------------------
The freeze operator binds the value of a non-atomic attribute at a specific trace
position to a variable (z) for use in a sub-formula.

    Syntax: z.(<formula>)
    Variable: Any value in the range a-z can be used as the identifier.

    - Examples:
          F a & x.("(x)x[V]<=34+7")
          F x.("(x)x[p]['b']==22")
          F x.("(x)x[p]['a']>0")
          F x.("(x)x[p]['a']>9")
          F x.("(x)'z' in x[att]")
          F x.(b & "(x)    x[p]['a']>9")
          a | b & x.("(x)x[V]==4 or x[V]==2")
          F b & x.(F y.(a & "(x,y)x[V]==y[V]"))
          F ((a | b) & z.((X false) & "(z)z[#] == 2"))
          F ((a | b) & z.((X false) & F y.("(z,y)z[#] == y[#]")))
          F x.(b & "(x)PROP.IN_DIC(x[p],'b',22)")
          F x.(b & "(x)PROP.IN_DIC_2(x,p,'b',22)")

Note 1: when using freeze variables, for instance 'x', to refer to specific 
        events the way to get access to the attributes will by means of expressions
        of the form "x[<attribute_name>]", a in the example before.

Note 2: By default, "my_propositions.py" is imported at booting time as "PROP". 
        This file is the place to write the Python functions used in the non-atomic propositions.
        In the examples, we are assuming that both, "IN_DIC" and "IN_DIC_2"
        are defined in "my_propositions.py".

================================================================================
RUNTIME COMMANDS AND MACROS
================================================================================

_SET (MACRO DEFINITION)
-----------------------
Defines a macro that is substituted before evaluation, generating a batch of formulas.

    Syntax: _SET ?id <comma_separated_list_of_values>

_WRITE (SAVE RESULTS)
---------------------
Saves all checked formula results to output files based on the log file name:
    - Checked formulas:           <log_file>.forms
    - Trace satisfiability (1/0): <log_file>.res
    - True state counts:          <log_file>.counts

_CLEAR_CHECKED (CLEAR HISTORY)
------------------------------
Clears the internal history of checked formulas and their results. This information
will be lost if not previously saved with _WRITE.


_LOAD
-----------------------
* This macro is used to dynamically load a file with python functions that could, since this instant, used in the formulas
* Example of use

$ _LOAD mp ./myNewPropositions.py

If, for instance, the content of "myNewPropositions.py" is 

----------------------------------
local M = {}

def isPos(x):
  return x[V] > 0

----------------------------------

the new loaded function could be used to check if a trace contains an event whose attribute 'V' of an event is positive, as follows:

$ F x.("(x)mp.isPos(x)")

or two events, with a positive and negative values, respectively:

$ F x.("(x)mp.isPos(x)" & F y.(!mp.isPos(y)))


_INFO (SHOW LOG INFO)
---------------------
Displays structural information about the currently loaded log model.

COMMENTS:
    - Formulas starting with a semicolon (;) are ignored (they are considered as comments).
    - Formulas starting with an at char (@) correspond to an OS call whose content is the formula but the first character (@)


================================================================================
OUTPUT FORMAT
================================================================================

When checking a formula, the result is output in a comma-separated format:

    <number_trues>,<number_falses>,<percentage_of_trues>,<checking_time_ms>

Example:
    DLTL -> f
    1,2,33.33,3.64

Meaning: 1 trace satisfied the formula, 2 did not, giving a 33.33% satisfaction
rate, with a checking time of 3.64 milliseconds.

# LTLSem

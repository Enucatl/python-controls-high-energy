#!/bin/bash

#define python startup variable

export PYTHONSTARTUP="./EIGER_Client_v3.py"

#try to run with ipython
if hash ipython 2>/dev/null; then
   ipython
else
   python
fi

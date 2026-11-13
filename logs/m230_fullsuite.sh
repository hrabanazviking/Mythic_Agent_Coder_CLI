#!/bin/bash
cd /home/volmarr/mythic-hammer/repo
export PYTHONPATH=/home/volmarr/mythic-hammer/repo
.venv-hammer/bin/python -m pytest tests/ -q > logs/m230-fullsuite.log 2>&1
echo "EXIT:$?" >> logs/m230-fullsuite.log
date +%s > logs/m230-fullsuite.done

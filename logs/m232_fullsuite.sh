#!/bin/bash
cd /home/volmarr/mythic-hammer/repo
export PYTHONPATH=/home/volmarr/mythic-hammer/repo
.venv-hammer/bin/python -m pytest tests/ -q > logs/m232-fullsuite.log 2>&1
echo "EXIT:$?" >> logs/m232-fullsuite.log
date +%s > logs/m232-fullsuite.done

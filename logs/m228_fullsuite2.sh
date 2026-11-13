#!/bin/bash
cd /home/volmarr/mythic-hammer/repo
export PYTHONPATH=/home/volmarr/mythic-hammer/repo
.venv-hammer/bin/python -m pytest tests/ -q > logs/m228-fullsuite2.log 2>&1
echo "exit=$?" >> logs/m228-fullsuite2.log

#!/bin/bash
cd /home/volmarr/mythic-hammer/repo
export PYTHONPATH=/home/volmarr/mythic-hammer/repo
.venv-hammer/bin/python -m pytest tests/ -q > logs/m227-fullsuite.log 2>&1
echo "exit=$?" >> logs/m227-fullsuite.log

#!/bin/bash
cd /home/volmarr/mythic-hammer/repo
export PYTHONPATH=/home/volmarr/mythic-hammer/repo
.venv-hammer/bin/python -m pytest tests/ -q > logs/m238-fullsuite-conf.log 2>&1
echo "EXIT:$?" >> logs/m238-fullsuite-conf.log
date +%s > logs/m238-fullsuite-conf.done

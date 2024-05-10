#!/bin/bash
cd distributedGPT

python3 multiple_machines.py --type server &

for i in {1..4}
do
    python3 multiple_machines.py --type client &
done

wait
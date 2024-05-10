#!/bin/bash
cd distributedGPT
python3 multiple_machines.py --type server --port 50052 &

sleep 5

for i in {1..4}
do
    python3 multiple_machines.py --type client --port 50052 &
done

wait
#!/bin/bash
run_in_terminal() {
    command="$1"
    gnome-terminal --command="bash -c '$command; exec bash'"
}

run_in_terminal "python3 multiple_machines.py --type server" &

for i in {1..4}
do
    run_in_terminal "python3 multiple_machines.py --type client" &
done

wait
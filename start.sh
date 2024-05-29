#!/bin/sh
python3 main.py "$@"
while [ -f .restart ];
do
  python3 main.py "$@"
  sleep 5
done

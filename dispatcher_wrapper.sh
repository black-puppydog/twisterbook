#! /bin/sh

for l in $(cat env-file.txt ); do export $l; done

./Dispatcher.py


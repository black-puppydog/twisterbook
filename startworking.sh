#! /bin/bash

ssh -f -L 3306:localhost:3306 root@178.62.162.119 -N
ssh -f -L 5672:localhost:5672 root@178.62.162.119 -N

docker start grave_ardinghelli

cd ~/twisterbook
/bin/bash -c ". ~/twister-env/bin/activate; exec /bin/bash -i"
C_FORCE_ROOT=1 celery -A TwisterScraper worker -l info

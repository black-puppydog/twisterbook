#! /bin/bash

ssh -f -L 3306:localhost:3306 root@$DB_SERVER -N
ssh -f -L 5672:localhost:5672 root@$DB_SERVER -N

celery -A TwisterScraper worker -l info

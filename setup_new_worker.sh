#! /bin/sh

export WORKER_IP=$1

ssh root@$WORKER_IP "docker stop scraping-worker"
ssh root@$WORKER_IP "docker rm scraping-worker"

ssh root@$WORKER_IP "mkdir /worker-build"

scp -r id_rsa id_rsa.pub Dockerfile env-file.txt envlistWrapper setup.sh start_scraper.sh TwisterScraper/ LoginData.py "$WORKER_IP:/worker-build/"

ssh root@$WORKER_IP "cd /worker-build && ./setup.sh $(curl http://169.254.169.254/metadata/v1/interfaces/public/0/ipv4/address)"



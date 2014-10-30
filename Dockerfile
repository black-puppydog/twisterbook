FROM python:3.3

RUN apt-get update \
&&  DEBIAN_FRONTEND=noninteractive apt-get install -y python3-pip \
&&  apt-get clean \
&&  rm -rf /var/lib/apt/lists/*
RUN pip install PyMySQL simplejson celery \
&&  pip install -e git+https://github.com/4tar/python-bitcoinrpc.git@p34-compatablity#egg=python-bitcoinrpc

ADD start_scraper.sh TwisterScraper LoginData.py

# celery would otherwise complain that we are running everything as root
ENV C_FORCE_ROOT 1

# needed to make the ssh tunnels
VOLUME /root/.ssh

CMD /start_scraper.sh

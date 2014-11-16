# run a cassandra instance that acts like locally-installed and stores its data in a volume
docker run -d -v /home/daan/code/twister/cassy-data:/var/lib/cassandra  --name cassy -p 0.0.0.0:22:22 -p 0.0.0.0:61621:61621 -p 0.0.0.0:7000:7000 -p 0.0.0.0:7001:7001 -p 0.0.0.0:7199:7199 -p 0.0.0.0:8012:8012 -p 0.0.0.0:9042:9042 -p 0.0.0.0:9160:9160 spotify/cassandra

# import data from a cassandra snapshot
./cassandra_init.py # set up schema
for f in $(ls -A1 twisterbook); do sstableloader -d 127.0.0.1 "twisterbook/$f"; done # has to be executed from the cassandra data folder

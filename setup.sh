#! /bin/sh

# launches a twister container and a scraper container
#
# USAGE: 
# setup.sh <server_address>


# install twister
docker pull miguelfreitas/twister
docker run --name twister -d --entrypoint="/twister-core/twisterd" miguelfreitas/twister -rpcuser=user -rpcpassword=pwd -printtoconsole

# generate an ssh key pair without passphrase and print the public key
mv id_rsa id_rsa.pub /root/.ssh/
chown -R root /root/.ssh/
chmod 600 /root/.ssh/id_rsa

#ssh-keygen -N '' -t rsa -f /root/.ssh/id_rsa
#echo "-----SSH PUBLIC KEY FOR WORKER-----"
#cat /root/.ssh/id_rsa.pub
#echo "-----------------------------------"

# add the server's publick key to the known_hosts so the ssh tunnels don't get a prompt
# echo the key for verification
echo "-----SSH PUBLIC KEY FOR SERVER CHECK THIS!-----"
ssh-keyscan $1 | tee /root/.ssh/known_hosts
echo "-----------------------------------------------"

docker build -t worker .
docker run -d --name scraping-worker -v /root/.ssh/:/root/.ssh/ -e "DB_SERVER=$1" --env-file=env-file.txt --link twister:twister worker

#! /bin/sh

# launches a twister container and a scraper container

# install twister
docker pull miguelfreitas/twister
docker run --name twister -d -P --entrypoint="/twister-core/twisterd" miguelfreitas/twister -rpcuser=user -rpcpassword=pwd -rpcallowip=172.17.42.1 -htmldir=/twister-html -printtoconsole

# generate an ssh key pair without passphrase and print the public key
ssh-keygen -N '' -t rsa -f /root/.ssh/id_rsa
echo "-----SSH PUBLIC KEY-----"
cat /root/.ssh/id_rsa.pub
echo "------------------------"

docker import worker.tar
docker run --name scraper -v /root/.ssh/:/root/.ssh/ --link twister:twister worker

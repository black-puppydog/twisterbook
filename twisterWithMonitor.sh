#! /bin/sh


# runs the twister daemon in my setup (i.e. ../twister-core/twisterd) with the right callback to keep the blockchain current in the database
../twister-core/twisterd -datadir=$HOME/.twister_2 -rpcthreads=6 -rpcuser=user -rpcpassword=pwd -rpcallowip=127.0.0.1 -rpcport=28332 -blocknotify="./BlockChainMonitor.py --only-block %s"


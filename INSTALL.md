Since there are a bunch of components to install and I don't have the necessary know-how (yet) to automate all of this, here are a bunch of steps that are necessary.
Let's hope I don't forget anything non-obvious...

# RabbitMQ
The Message queue will be needed to distribute scraping tasks.
* set up the docker from dockerfile/rabbitmq or install locally
    * `docker pull dockerfile/rabbitmq`
    * `docker run -d -p 127.0.0.1:5672:5672 -p 127.0.0.1:15672:15672 dockerfile/rabbitmq`
* replace the guest:guest login with a proper admin account
    * since we configured the rabbitmq server to only accept connections from localhost, we need to tunnel the traffic for the weg ui  over ssh:
        * on your local machine, execute `ssh -D 7070 root@servername`
        * configure your browser to use 127.0.0.1 as a socks proxy. make sure to remove any exception for the host 127.0.0.1, since that is exactly what we want. also make sure you remember what the settings were before you changed them or your browser will soon be a sad place ;)
    * visit http://localhost:15672 and login with guest:guest
    * create new admin user
    * log out
    * log in with new admin user
    * delete guest account
* create new user taskPublisher
    * give it all permissions on the queue-regex "scraping"
    * enter the taskPublisher and its password into the env-file.txt file that the envlistWrapper uses:
        * RABBITMQ_PASSWORD=<pw>

# Source the right virtualenv
This might be unneccessary/harmful for a docker container, but for a local PC it is a good idea.
* create a new virtualenv if needed:
    * `virtualenv -p python3.3 twister-env`
* source the bin/activate from the virtualenv
* then install the dependencies from requirements.txt:
    * `pip install -r requirements.txt`
    * **todo: this will give a warning because we cannot compile simplecson in C. which libs are needed?**

# Start the twister daemon with user registration callback
This is very specific to my folder structure atm, but really it's just the "../twister-core" prefix that would need changing.
* Start the script `./envlistWrapper ./twisterWithMonitor.sh`.
    * This starts twisterd with the callback script "BlockChainMonitor.py --only-block %s" which means that every new block will automatically be entered into the database.
* *Now* we can start the initial import process for the existing users:
    * `./BlockChainMonitor.py`
    * This can be done as often as it pleases us, since it does not change existing users.
    * If you suspect there might be a block missing from the database, there is the --only-block option which takes a single hash value as an argument

# Start Workers locally
`./envlistWrapper celery -c 10 -A TwisterScraper worker -l info`
This uses 10 workers, which only works when using the torrent scraping method.
For DHT scraping this would likely lock up the daemon very quickly so use a smaller number, like 2 or 3 per scraper. Not sure yet how to choose this well or why the daemon locks up in the first place.

# Start Task Dispatcher
Later-on we want this to happen on a regular basis, but so far we can just run the Dispatcher by hand:
`./envlistWrapper ./Dispatcher.py`
This will (at the moment) only refresh already known-active users and new users.
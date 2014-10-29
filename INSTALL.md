Since there are a bunch of components to install and I don't have the necessary know-how (yet) to automate all of this, here are a bunch of steps that are necessary.
Let's hope I don't forget anything non-obvious...

# MySQL
MySQL will hold the scraped posts and profiles for now.
Later I would like to use a proper full text search engine for this, probably SolR with a cassandra backend, i.e. Solandra.
* Enter the commands from SQL-reminders.md

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
    * enter the taskPublisher and its password into LoginData.py

# Source the right virtualenv
This might be unneccessary/harmful for a docker container, but for a local PC it is a good idea.
* create a new virtualenv if needed:
    * `virtualenv -p python3.3 twister-env`
* source the bin/activate from the virtualenv
* then install the dependencies from requirements.txt:
    * `pip install -r requirements.txt`
    * **todo: this will give a warning because we cannot compile simplecson in C which libs are needed?**

# start the monitoring twisterd
Since we want the "newblock" callback from twisterd, we cannot user the container verbatim. At a later stage I should make a new container based off the official one. For now, we need to compile twister from scratch.
* go to `twister-core` folder and follow the install instructions from the `doc/` folder
    * on DigitalOcean there seems to be a problem with the locale `LC_ALL`, it needs to be properly set in `/etc/environment`

Now we start the twister daemon.
This is very specific to my folder structure atm, but really it's just the "../twister-core" prefix that would need changing.
* Start the script `./twisterWithMonitor.sh`.
    * This starts twisterd with the callback script "BlockChainMonitor.py --only-block %s" which means that every new block will automatically be entered into the database.
* *Now* we can start the initial import process for the existing users:
    * `./BlockChainMonitor.py`
    * This can be done as often as it pleases us, since it does not change existing users.

# Start Workers
Make a new DigitalOcean server with Docker, pull the twister image and start an instance.
Or clone the twister-core git repository and user the `twister-on-docker` script.

we need to farward the two ports for the rabbitMQ and the MySQL servers because we didn't bother to make them secure. Instead, we just limited them so that they only accept local connections.
So we create an ssh kaypair *without a passphrase* on the worker node, and copy the publick key into the `~/.ssh/authorized_keys`.
Then we forward the ports with
* `ssh root<database_server> -L 5672:localhost:5672 -N`
* `ssh root<database_server> -L 3306:localhost:3306 -N`

Finally, we start the workers with `C_FORCE_ROOT` set to make celery accept that we are root.
* `C_FORCE_ROOT=1 celery -A TwisterScraper worker -l info`

# Start Task Dispatcher
Later-on we want this to happen on a regular basis, but so far we can just run the Dispatcher by hand:
    `./Dispatcher.py`

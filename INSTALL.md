Since there are a bunch of components to install and I don't have the necessary know-how (yet) to automate all of this, here are a bunch of steps that are necessary.
Let's hope I don't forget anything non-obvious...

# MySQL
MySQL will hold the scraped posts and profiles for now.
Later I would like to use a proper full text search engine for this, probably SolR with a cassandra backend, i.e. Solandra.
* Set up a docker container or install locally
* enter the commands from SQL-reminders.md

# RabbitMQ
The Message queue qill be needed to distribute scraping tasks.
* set up the docker from dockerfile/rabbitmq or install locally
* replace the gues:guest login with a proper admin account
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
* or create a new virtualenv if needed:
    * `virtualenv -p python3.3 twister-env`
    * then install the dependencies from requirements.txt
* source the bin/activate from the virtualenv

# start the monitoring twisterd
This is very specific to my folder structure atm, but that;s really just the "../twister-core" prefix that would need changing.
* Start the script `./twisterWithMonitor.sh`.
    * This starts twisterd with the callback script "BlockChainMonitor.py --only-block %s" which means that every new block will automatically be entered into the database.
* *Now* we can start the initial import process for the existing users:
    * `./BlockChainMonitor.py`
    * This can be done as often as it pleases us, since it does not change existing users.

# Start Workers
For now we run the workers on one node: localhost
Start them with `celery -A TwisterScraper worker -l info`

# Start Task Dispatcher
Later-on we want this to happen on a regular basis, but so far we can just run the Dispatcher by hand:
    ./Dispatcher.py

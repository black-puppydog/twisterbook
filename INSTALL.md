Since there are a bunch of components to install and I don't have the necessary know-how (yet) to automate all of this, here are a bunch of steps that are necessary.
Let's hope I don't forget anything non-obvious...

# MySQL
* Set up a docker container or install locally
* enter the commands from SQL-reminders.md

# RabbitMQ
* set up the docker from dockerfile/rabbitmq or install locally
* replace the gues:guest login with a proper admin account
    * visit http://localhost:15672 and login with guest:guest
    * create new admin user
    * log out
    * log in with new admin user
    * delete guest account
* create new user taskPublisher
    * give it all permissions on the queue-regex "scraping"
* create new user taskConsumer
    * give it only read permission on the queue-regex "scraping"


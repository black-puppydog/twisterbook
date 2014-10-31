# Deployment

* finish dockerizing workers
    * docker image + dockerfile must not contain private/dynamic information
        * twister IP+port
        * mysql user/pw (ip not an issue since we use ssh tunnels)
        * rabbitmq user/pw
        * server public ssh key
        * workers ssh key pair
* what can be automated for server setup
    * is that even an issue? after all, with mysql there is but one server.
* can I start net scrapers as they are needed?
    * control digitalocean costs
    * Danger! set hard limits or there will be bugs that crash my credit card!

# Components

## HTML/JS UI
* do that.
* Seriously, do that, the whole thing is pretty pointless without it.
* Just hack *something* together at first, then iterate. It'll be fine. :)

## Dispatcher
* find good strategy for triggering scrapes
    * timeout (scrape profiles every $N seconds)
        * different for active/inactive users 
            * **how are these defined?**
    * following certain #hashtags?
    * listening to mentions @user that we control?
    * make use of new scraper task for specific posts (see below)
* find posts that we suspiciously miss
    * posts we only have replies/RTs of, but not the post itself
        * see `useful_queries.sql`
* configure to run at scheduled intervals
    * cronjob?
    * celery itself?

## Search and Indexing
* consider changing back to cassandra for storage
    * scalable in case of network/activity growth

## Database Layout
* create new fields for users
    * registration time
    * registration block height
    
## Scraper
* create task to scrape specific posts only
    * pass dict(username: list(k)) and scrape only these posts
* get downloading of posts via torrent working!
    * utopian vision: 
        * scrapers follow a number of torrents
        * when we want to refresh a user, we give the task to a worker which already has the torrent
        * INCREDIBLE SPEED! :)

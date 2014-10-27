# Architecture

* how do the results go from the scrapers into the solrfeeder?
    * by returning a result to the dispatcher?
        * bottleneck at dispatcher --> no!
    * direct rpc (twisted? celery?) to the solrfeeder process?
    * direct call to solr itself, removing Solrfeeder altogether?

# Deployment

* how do I deploy all the different components?
    * which component runs on which machine?
    * deployment via docker?
        * how/what to automate?
* can I start net scrapers as they are needed?
    * control digitalocean costs
    * Danger! set hard limits or there will be bugs that crash my credit card!

# Components

## Celery: Dispatcher and Scrapers

* configure the dispatcher to run at scheduled intervals
* how can we have persistent state (i.e. twister session) in a worker?

## Search and Indexing

* is SolR really the best alternative I have?
    * does it scale?
    * are there alternatives that use cassandra?
        * lucene directly?
        * datastax API
            * student licenses?

# Security

* how do I make sure that no service except the HTML interface are publickly available?
    * set passwords for...
        * SolR
        * Cassandra
        * Workers
        * ...?

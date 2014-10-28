__author__ = 'daan'

"""
This script starts all the components of the search engine on the current machine:
* QueueBuilder
* ScrapingTaskDispatcher
* One Scraper
* SolrFeeder

Every component is started as a separate process (forked) so that they are all isolated from one another.
The script then runs a loop in which one can make simple queries to the system in a CLI.

On exit, all the components are terminated so that no processes stay behind.
"""

from multiprocessing.pool import Pool



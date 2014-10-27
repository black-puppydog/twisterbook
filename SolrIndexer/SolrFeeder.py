__author__ = 'daan'

import pysolr


class Feeder:

    def __init__(self, url='http://localhost:8983/solr/'):
        self.url = url
        self.solr = pysolr.Solr(self.url, timeout=10)

    def index_posting(self, posting):
        self.index_postings([posting])

    def index_postings(self, postings):
        self.solr.add(postings)

import pysolr

__author__ = 'daan'


class Searcher:

    def __init__(self, url='http://localhost:8983/solr/'):
        self.url = url
        self.solr = pysolr.Solr(self.url, timeout=10)

    def search_freetext(self, text):
        return self.solr.search(text)

"""Module with an API for MediaWikis."""

import re

from urllib.parse import quote

def select_singleton_list(lst):
    assert len(lst) == 1

    return lst[0]

def select_singleton_dict(d):
    return select_singleton_list(list(d.values()))

def query_json(path, json):
    result = json

    for part in path:
        if callable(part):
            result = part(result)
        else:
            result = result[part]

    return result

class MediaWikiSession(object):
    """Encapsulates a session for requests to a MediaWiki server. This class
    implements all methods which are related to HTTP requests."""

    def __init__(self, domain, req):
        """Initializes the object.

        Arguments:
        domain -- domain of the MediaWiki, e.g. `"de.wikibooks.org"`
        req    -- an session object of the `request` framework
        """
        self.domain = str(domain)
        self.req = req

    @property
    def index_url(self):
        """Returns the URL to the server's `index.php` file."""
        return "http://" + self.domain + "/w/index.php"

    def index_call(self, params):
        """Make an HTTP request to the server's `index.php` file."""
        return self.req.get(self.index_url, params=params).text

    @property
    def api_url(self):
        """Returns the URL to the server's `api.php` file."""
        return "http://" + self.domain + "/w/api.php"

    def api_call(self, params):
        """Make an HTTP request to the server's `api.php` file."""
        params["format"] = "json"

        return self.req.get(self.api_url, params=params).json()

    def api_query(self, title, params, path):
        """Make a query action against the server's API. """
        params["action"] = "query"

        json = self.api_call(params)
        result = query_json(["query"] + path, json)

        if "query-continue" in json:
            cont_path = ["query-continue", select_singleton_dict]

            params.update(query_json(cont_path, json))

            result += self.query(path, params)

        return result

    def pageviews(self, title, start, end):
        """Return page views of article `title` in the range `start` to `end`.
        `start` and `end` must be strings in the Format YYYYMMDD.
        """
        url = "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/"
        url += self.domain
        url += "/all-access/all-agents/"
        url += quote(title, safe="")
        url += "/daily/" + start + "/" + end

        result = self.req.get(url).json()

        if "items" in result:
            return sum((int(x["views"]) for x in result["items"]))
        else:
            return 0

class MediaWikiAPI(object):
    """Implements an API for content stored on a MediaWiki."""

    def __init__(self, session):
        """Initializes the object.

        Arguments:
        session -- an object of the class `MediaWikiSession`
        """
        self.session = session

    def get_content(self, title):
        """Returns the content of an article with title `title`."""
        return self.session.index_call({"action": "raw", "title": title})

    def revisions(self, title):
        params = {
            "titles": title,
            "prop": "revisions",
            "rvprop": "timestamp|user|size|comment",
            "rvlimit": "max"
        }
        
        try:
            return self.session.api_query(title, params,
                ["pages", select_singleton_dict, "revisions"])
        except KeyError:
            return []

    def revisions_count(self, title, start, end):
        return len([x for x in self.revisions(title) if x["timestamp"] >= start and x["timestamp"] < end])

    def all_titles(self, title):
        """Returns a set of all titles the article `title` had in the past."""
        result = set()

        result.add(title)

        re_link = "\\[\\[([^\\]]+)\\]\\]"
        re1 = ".*verschob die Seite %s nach %s.*" % (re_link, re_link)
        re2 = ".*hat „%s“ nach „%s“ verschoben.*" % (re_link, re_link)
        regs = [ re.compile(re1), re.compile(re2) ]

        for x in self.revisions(title):
            comment = x.get("comment", "")

            if "comment" not in x:
                comment = x["commenthidden"]

            for reg in regs:
                m = reg.match(comment)

                if m:
                    result.add(m.group(1))
                    result.add(m.group(2))

        return result

    def pageviews(self, title, start, end):
        """Return page views of article `title` in the range `start` to `end`.
        `start` and `end` must be strings in the Format YYYYMMDD.
        """
        return sum((self.session.pageviews(x, start, end) for x in self.all_titles(title)))

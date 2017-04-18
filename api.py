"""Module with an API for MediaWikis."""

from urllib.parse import quote

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

    def pageviews(self, title, start, end):
        """Return page views of article `title` in the range `start` to `end`.
        `start` and `end` must be strings in the Format YYYYMMDD.
        """
        return self.session.pageviews(title, start, end)

"""
Provides a high level interface to the Ship issue tracking REST scripting API.
"""

import sys
import os

try:
    import requests
except:
    sys.stderr.write("Requests library is required. python3 -m pip install requests. See http://requests.readthedocs.org/en/latest/user/install/#install\n")
    sys.exit(1)

class api:
    """
    Encapsulates all interactions with the Ship API.
    """

    def __init__(self, token=None, server="https://api.realartists.com"):
        """
        Initialize a new api object. Pass in an API token or omit it to read SHIP_API_TOKEN from
        your environment.
        """
        
        self.API_VERSION = "20151105"
        self.server = server
        if token is not None:
            self.token = token
        else:
            self.token = os.getenv("SHIP_API_TOKEN")
            if self.token is None:
                raise Error("Cannot find SHIP_API_TOKEN in environment. We need this.")
    
    def url(self, endpoint):
        return "%s/api/%s/%s" % (self.server, self.API_VERSION, endpoint)
        
    def headers(self):
        return { "Authorization" : self.token }
    
    def problem(self, identifier):
        """
        Fetch a problem.
        identifier should be an int representing the problem identifier to fetch.
        """

        r = requests.get(self.url("problems/%d" % identifier), headers=self.headers())
        r.raise_for_status()
        return r.json()
    
    def search(self, predicate=None, savedQueryURL=None):
        """
        Search for a set of problems given a predicate.
        Predicate is an NSPredicate formatted string.
        SavedQueryURL is a query URL copied from the Ship client like this: ship://Query/2Kk8ww70TvWEyVO3bzYpkQ <Enhance!>
            You can copy a query URL in the Ship client app by selecting a saved query and right (ctrl) clicking and choosing Copy Query URL.
        """
        
        headers = self.headers()
        headers["Content-Type"] = "application/json"
        params = {}
        if predicate is not None:
            params["predicate"] = predicate
        elif savedQueryURL is not None:
            params["savedQuery"] = savedQueryURL
        else:
            raise Error("Either predicate or savedQueryURL is required to do a search")
                    
        r = requests.get(self.url("problems/search"), headers=headers, params=params)
        r.raise_for_status()
        return r.json()

            
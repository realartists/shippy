"""
Provides a high level interface to the Ship issue tracking REST scripting API.
For additional documentation, please refer to 
https://www.realartists.com/docs/api/index.html
"""

import sys
import os
import requests

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
        
    def post_headers(self):
        return { "Authorization" : self.token, "Content-Type" : "application/json" }
            
    def me(self):
        """
        Return the user represented by the active API token.
        """        
        return self.users("identifier == $ApiUser")
    
    def active_users(self):
        return self.users("inactive == NO")
    
    def users(self, predicate=None):
        """
        Return the list of users, optionally filtered by a predicate.
        """
                
        if predicate is None:
            r = requests.get(self.url("users"), headers=self.headers())
        else:
            r = requests.get(self.url("users/search"), params={"predicate":predicate}, headers=self.headers())
        r.raise_for_status()
        return r.json()
        
    def components(self, predicate=None):
        """
        Return the list of components, optionally filtered by a predicate.
        """
        
        if predicate is None:
            r = requests.get(self.url("components"), headers=self.headers())
        else:
            r = requests.get(self.url("components/search"), params={"predicate":predicate}, headers=self.headers())
        r.raise_for_status()
        return r.json()
    
    def component_parent(self, component):
        """
        Returns the component that is the parent of the passed in component.
        """
        
        list = self.components("ANY children.identifier = '%s'" % _obj_id(component))
        if len(list) > 0:
            return list[0]
        else:
            return None
    
    def component_children(self, component):
        """
        Returns the immediate child components of the passed in component
        """        
        return self.components("parent.identifier = '%s'" % _obj_id(component))
        
    def classifications(self):
        """
        Returns the list of allowed problem classifications
        """
        
        r = requests.get(self.url("classifications"), headers=self.headers())
        r.raise_for_status()
        return r.json()
    
    def milestones(self, predicate=None):
        """
        Return the list of all milestones, optionally filtered by a predicate 
        """
        
        if predicate is None:
            r = requests.get(self.url("milestones"), headers=self.headers())
        else:
            r = requests.get(self.url("milestones/search"), params={"predicate":predicate}, headers=self.headers())
        r.raise_for_status()
        return r.json()
        
    def active_milestones(self, within_component=None):
        if within_component is not None:
            if isinstance(within_component, str):
                within_component = self.components("identifier = %s" % within_component)[0]
            predicate = """
                (StartDate == nil || StartDate < NOW()) 
                AND 
                (EndDate == nil || EndDate > NOW()) 
                AND
                (component.identifier == nil OR %s BEGINSWITH component.fullName)
            """
            return self.milestones(predicate % (_obj_id(within_component), within_component["fullName"]))
        else:
            predicate = """
                (StartDate == nil || StartDate < NOW()) 
                AND 
                (EndDate == nil || EndDate > NOW())
            """
            return self.milestones(predicate)
            
    def priorities(self):
        """
        Returns the list of priorities
        """
        
        r = requests.get(self.url("priorities"), headers=self.headers())
        r.raise_for_status()
        return r.json()
    
    def states(self, predicate=None):
        """
        Returns the list of states
        """
        
        if predicate is None:
            r = requests.get(self.url("states"), headers=self.headers())
        else:
            r = requests.get(self.url("states/search"), params={"predicate":predicate}, headers=self.headers())
        r.raise_for_status()
        return r.json()
        
    def initial_state(self):
        """
        Returns the first start state
        """
        return self.initial_states()[0]
        
    def initial_states(self):
        """
        Returns the list of start states
        """
        return self.states("Initial = YES")
    
    def state_transitions(self, state):
        """
        Return the list of valid state transitions from state.
        """
        return self.states("ANY PreviousStates.identifier = '%s'" % _obj_id(state))
        
    
    def problem(self, identifier):
        """
        Fetch a single problem.
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
        
    def create_problem(self, problem):
        """
        Create a new problem based on the provided problem data.
        """
        
        r = requests.post(self.url("problems"), headers=self.post_headers(), json=problem)
        r.raise_for_status()
        return r.json()
        
        
def _obj_id(obj):
        if isinstance(obj, str):
            return obj
        else:
            return obj["identifier"]


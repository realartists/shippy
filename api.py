import sys
import os
import requests

try:
    from urllib.request import quote
except:
    from urllib import quote

class Api:
    """
    Provides an interface to the Ship issue tracking REST scripting API.
    For additional documentation, please refer to 
    https://www.realartists.com/docs/api/index.html
    """

    def __init__(self, token=None, dry_run=False, server="https://api.realartists.com"):
        """
        Initialize a new api object. Pass in an API token or omit it to read SHIP_API_TOKEN from
        your environment.
        
        Args:
            token (str): Your API token. Get this from the Administration menu in Ship.
            dry_run (boolean): Set to True if you want the shipapi to merely log every change it would make, but not actually change anything on the server.
        """
        
        self.API_VERSION = "20151105"
        self.server = server
        self.dry_run = dry_run
        if token is not None:
            self.token = token
        else:
            self.token = os.getenv("SHIP_API_TOKEN")
            if self.token is None:
                raise Exception("Cannot find SHIP_API_TOKEN in environment. We need this.")
    
    def _url(self, endpoint):
        return "%s/api/%s/%s" % (self.server, self.API_VERSION, endpoint)
        
    def _headers(self):
        return { "Authorization" : self.token }
        
    def _post_headers(self):
        return { "Authorization" : self.token, "Content-Type" : "application/json" }
        
    def _post(self, endpoint, json=None):
        if self.dry_run:
            print("DRY RUN: POST %s" % endpoint)
            return _DryRunRequest()
            
        r = requests.post(self._url(endpoint), headers=self._post_headers(), json=json)
        r.raise_for_status()
        return r
        
    def _patch(self, endpoint, json=None):
        if self.dry_run:
            print("DRY RUN: PATCH %s" % endpoint)
            return _DryRunRequest()

        r = requests.patch(self._url(endpoint), headers=self._post_headers(), json=json)
        r.raise_for_status()
        return r
    
    def _put(self, endpoint, json=None):
        if self.dry_run:
            print("DRY RUN: PUT %s" % endpoint)
            return _DryRunRequest()

        r = requests.put(self._url(endpoint), headers=self._post_headers(), json=json)
        r.raise_for_status()
        return r
            
    def _delete(self, endpoint, json=None):
        if self.dry_run:
            print("DRY RUN: DELETE %s" % endpoint)
            return _DryRunRequest()

        r = requests.delete(self._url(endpoint), headers=self._headers(), json=json)
        r.raise_for_status()
    
    def _get(self, endpoint, params=None):
        r = requests.get(self._url(endpoint), params=params, headers=self._headers())
        r.raise_for_status()
        return r
        
    def me(self):
        """Return the user represented by the active API token."""        
        return self.users("identifier == $ApiUser")
    
    def users_active(self):
        """Returns the list of users that have accounts in good standing with the organization
        (that is, they have not left the organization and have not been marked as inactive
        by an admin)."""
        return self.users("inactive == NO")
    
    def users(self, predicate=None):
        """Return the list of users, optionally filtered by a predicate."""
                
        if predicate is None:
            return self._get("users").json()
        else:
            return self._get("users/search", params={"predicate":predicate}).json()
        
    def components(self, predicate=None):
        """Return the list of components, optionally filtered by a predicate."""
        
        if predicate is None:
            return self._get("components").json()
        else:
            return self._get("components/search", params={"predicate":predicate}).json()
    
    def component_parent(self, component):
        """Returns the component that is the parent of the passed in component."""
        
        list = self.components("ANY children.identifier = '%s'" % _obj_id(component))
        if len(list) > 0:
            return list[0]
        else:
            return None
    
    def component_children(self, component):
        """Returns the immediate child components of the passed in component"""        
        return self.components("parent.identifier = '%s'" % _obj_id(component))
        
    def classifications(self):
        """Returns the list of allowed problem classifications"""
        return self._get("classifications").json()
    
    def milestones(self, predicate=None):
        """Return the list of all milestones, optionally filtered by a predicate"""
        
        if predicate is None:
            return self._get("milestones").json()
        else:
            return self._get("milestones/search", params={"predicate":predicate}).json()
        
    def milestones_active(self, within_component=None):
        """
        Returns only the milestones that are currently active (that is, those that
        either omit the start and end dates, or those with start and end dates where
        start < now < end).
        """
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
        """Returns the list of priorities"""
        return self._get("priorities").json()
    
    def states(self, predicate=None):
        """Returns the list of states"""
        
        if predicate is None:
            return self._get("states").json()
        else:
            return self._get("states/search", params={"predicate":predicate}).json()
        
    def state_initial(self):
        """Returns the first start state"""
        return self.states_initial()[0]
        
    def states_initial(self):
        """Returns the list of all start states"""
        return self.states("Initial = YES")
    
    def state_transitions(self, state):
        """Return the list of valid state transitions from state."""
        return self.states("ANY PreviousStates.identifier = '%s'" % _obj_id(state))
        
    
    def problem(self, identifier):
        """
        Fetch a single problem.
        identifier should be an int representing the problem identifier to fetch.
        """
        return self._get("problems/%d" % identifier).json()
    
    def problem_search(self, predicate=None, savedQueryURL=None):
        """
        Search for a set of problems given a predicate.
        Predicate is an NSPredicate formatted string.
        SavedQueryURL is a query URL copied from the Ship client like this: ship://Query/2Kk8ww70TvWEyVO3bzYpkQ <Enhance!>
            You can copy a query URL in the Ship client app by selecting a saved query and right (ctrl) clicking and choosing Copy Query URL.
        """
        
        params = {}
        if predicate is not None:
            params["predicate"] = predicate
        elif savedQueryURL is not None:
            params["savedQuery"] = savedQueryURL
        else:
            raise Error("Either predicate or savedQueryURL is required to do a search")
                    
        return self._get("problems/search", params=params).json()
        
    def problem_create(self, problem):
        """
        Create a new problem based on the provided problem data.
        """        
        return self._post("problems", json=problem).json()
        
    def problem_update(self, identifier, updates):
        """
        Update an existing problem.
        
        Args:
            identifier (int): the problem identifier
            updates (dict): 
                A dictionary following the same schema as returned from the problem 
                method, but only including the fields that you wish to update.
                
        Returns:
            The updated problem as a dict.
        
        Example:
            # Close Problem #1
            closed = api.states(predicate="name = 'Closed'")[0]
            api.update_problem(1, { "state" : closed })
        """
        return self._patch("problems/%d" % identifier, json=updates).json()
        
    def problem_keyword_set(self, identifier, keyword, value=None):
        """
        Update an existing problem and add/update a keyword.
        
        Args:
            identifier (int): the problem identifier
            keyword (string): the keyword to add
            value (string): (Optional), the value to set the keyword to.
            
        Returns:
            None
        """
        self._put("problems/%d/keywords/%s" % (identifier, quote(keyword, safe="")), json=value)
    
    def problem_keyword_delete(self, identifier, keyword):
        """
        Update an existing problem and remove a keyword.
        
        Args:
            identifier (int): the problem identifier
            keyword (string): the existing keyword to remove
        
        Returns:
            None
        """
        self._delete("problems/%d/keywords/%s" % (identifier, quote(keyword, safe="")))
    
    def problem_relationships(self, identifier):
        """
        Returns the set of relationships that the provided problem is a part of.
        
        Args:
            identifier (int): the problem identifier
            
        Returns:
            A list of relationships represented as dicts.
        """
        return self._get("problems/%d/relationships" % identifier).json()

    def problem_relationship_add(self, src_identifier, relation_type, dst_identifier):
        """
        Create a relationship between two problems.
        
        It is only necessary to establish one side of the relationship. The complimentary side of the relationship will be established automatically by the server.
        
        Args:
            src_identifier (int): the source problem identifier
            relation_type (str): the type of relationship to establish. See the RelationType* constants in this module for acceptable values.
            dst_identifier (int): the destination problem identifier.
        
        Returns:
            None
        """
        self._put("problems/%d/relationships" % src_identifier, json={"type" : relation_type, "problemIdentifier" : dst_identifier })
    
    def problem_relationship_delete(self, src_identifier, relation_dict):
        """
        Delete a relationship as returned by problem_relationships.
        
        Args:
            src_identifier (int): the problem identifier
            relation_dict (dict): in this form: { "problemIdentifier" : dst_identifier, "type" : RelationType* }
        
        Returns:
            None
        """
        self._delete("problems/%d/relationships" % src_identifier, json=relation_dict)
        
    def problem_comments(self, identifier):
        """
        Access the list of comments on the requested problem.
        
        Args:
            identifier (int): the problem identifier
            
        Returns:
            An array of dicts describing the comments
        """
        return self._get("problems/%d/comments" % identifier).json()
    
    def problem_comments_append(self, identifier, comment, html=None):
        """
        Append a plain text comment to the problem.
        
        Args:
            identifier (int): the problem identifier
            comment (str): the comment text
            html (str) (optional): HTML representation of the comment
            
        Returns:
            None
        """
        params = {"text": comment}
        if html is not None:
            params["html"] = html
        
        self._post("problems/%d/comments" % identifier, json=params)
        
    def problem_watchers(self, identifier):
        """
        Access the list of users watching the indicated problem.
        
        Args:
            identifier (int): the problem identifier
            
        Returns:
            An array of dicts describing the users watching the problem.
        """
        return self._get("problems/%d/watchers" % identifier).json()
    
    def problem_watchers_add(self, identifier, user):
        """
        Add the specified user to the list of users watching the indicated problem:
        
        Args:
            identifier (int): the problem identifier
            user (dict or str): 
                either a dict object describing a user as returned from Api.users(...)
                or a str representing either the user identifier or the user email
            
        Returns:
            None
        """
        
        params = {}
        if isinstance(user, str):
            if user.find('@') != -1:
                params["email"] = user
            else:
                params["identifier"] = user
        else:
            params = user
            
        self._put("problems/%d/watchers" % identifier, json=params)


RelationTypeRelatedTo = "RelatedTo"
RelationTypeParentOf = "ParentOf"
RelationTypeChildOf = "ChildOf"
RelationTypeOriginalOf = "OriginalOf"
RelationTypeDuplicateOf = "DuplicateOf"
RelationTypeCauseOf = "CauseOf"
RelationTypeCausedBy = "CausedBy"
RelationTypeBlockerOf = "BlockerOf"
RelationTypeBlockedBy = "BlockedBy"
RelationTypeClonedTo = "ClonedTo"
RelationTypeClonedFrom = "ClonedFrom"

def _obj_id(obj):
        if isinstance(obj, str):
            return obj
        else:
            return obj["identifier"]

class _DryRunRequest(object):
    def json(self):
        return {}

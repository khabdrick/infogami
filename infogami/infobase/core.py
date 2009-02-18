"""Core datastructures for Infogami.
"""
import web

class InfobaseException(Exception):
    status = "500 Internal Server Error"
    pass
    
class NotFound(InfobaseException):
    status = "404 Not Found"
    def __init__(self, key):
        InfobaseException.__init__(self, 'Not Found: %s' % repr(web.safeunicode(key)))
        
class PermissionDenied(InfobaseException):
    status = "403 Forbidden"
    pass

class BadData(InfobaseException):
    status = "400 Bad Request"
    pass
    
class TypeMismatch(BadData):
    def __init__(self, type_expected, type_found):
        BadData.__init__(self, "Expected %s, found %s" % (repr(type_expected), repr(type_found)))

class Text(unicode):
    """Python type for /type/text."""
    def __repr__(self):
        return "<text: %s>" % unicode.__repr__(self)
        
class Reference(unicode):
    """Python type for reference type."""
    def __repr__(self):
        return "<ref: %s>" % unicode.__repr__(self)

class Thing:
    def __init__(self, store, key, data):
        self._store = store
        self.key = key
        self._data = data

    def _process(self, value):
        if isinstance(value, list):
            return [self._process(v) for v in value]
        elif isinstance(value, dict):
            return web.storage((k, self._process(v)) for k, v in value.iteritems())
        elif isinstance(value, Reference):
            return self._store.get(value)
        else:
            return value

    def __contains__(self, key):
        return key in self._data

    def __getitem__(self, key):
        return self._process(self._data[key])

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError, key
            
    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default

    def __repr__(self):
        return "<thing: %s>" % repr(self.key)
        
    def copy(self):
        return Thing(self._store, self.key, self._data.copy())
        
    def _get_data(self):
        import copy
        return copy.deepcopy(self._data)

    def format_data(self):
        import common
        return common.format_data(self._get_data())

    def get_property(self, name):
        for p in self.get('properties', []):
            if p.get('name') == name:
                return p
        
    @staticmethod
    def from_json(store, key, data):
        import _json as simplejson
        return Thing.from_dict(store, key, simplejson.loads(data))
        
    @staticmethod
    def from_dict(store, key, data):
        import common
        data = common.parse_query(data)        
        return Thing(store, key, data)

class Store:
    """Storage for Infobase.
    
    Store manages one or many SiteStores. 
    """
    def create(self, sitename):
        """Creates a new site with the given name and returns store for it."""
        raise NotImplementedError
        
    def get(self, sitename):
        """Returns store object for the given sitename."""
        raise NotImplementedError
    
    def delete(self, sitename):
        """Deletes the store for the specified sitename."""
        raise NotImplementedError

class SiteStore:
    """Interface for Infobase data storage"""
    def get(self, key, revision=None):
        raise NotImplementedError
        
    def new_key(self, type, kw):
        """Generates a new key to create a object of specified type. 
        The store guarentees that it never returns the same key again.
        Optional keyword arguments can be specified to give more hints 
        to the store in generating the new key.
        """
        import uuid
        return '/' + str(uuid.uuid1())
        
    def get_many(self, keys):
        return [self.get(key) for key in keys]
    
    def write(self, query, timestamp=None, comment=None, machine_comment=None, ip=None, author=None):
        raise NotImplementedError
        
    def things(self, query):
        raise NotImplementedError
        
    def versions(self, query):
        raise NotImplementedError
        
    def get_user_details(self, key):
        """Returns a storage object with user email and encrypted password."""
        raise NotImplementedError
        
    def update_user_details(self, key, email, enc_password):
        """Update user's email and/or encrypted password.
        """
        raise NotImplementedError
            
    def find_user(self, email):
        """Returns the key of the user with the specified email."""
        raise NotImplementedError
        
    def register(self, key, email, encrypted):
        """Registers a new user.
        """
        raise NotImplementedError
        
    def transact(self, f):
        """Executes function f in a transaction."""
        raise NotImplementedError
        
    def initialze(self):
        """Initialzes the store for the first time.
        This is called before doing the bootstrap.
        """
        pass
        
    def set_cache(self, cache):
        pass

class Event:
    """Infobase Event.
    
    Events are fired when something important happens (write, new account etc.).
    Some code can listen to the events and do some action (like logging, updating external cache etc.).
    """
    def __init__(self, sitename, name, timestamp, ip, username, data):
        """Creates a new event.
        
        sitename - name of the site where the event is triggered.
        name - name of the event
        timestamp - timestamp of the event
        ip - client's ip address
        username - current user
        data - additional data of the event
        """
        self.sitename = sitename
        self.name = name
        self.timestamp = timestamp
        self.ip = ip
        self.username = username
        self.data = data

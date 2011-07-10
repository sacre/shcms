# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
from datetime import datetime
from google.appengine.ext import db
from google.appengine.api import memcache
import yaml, logging
import settings
import webapp2
log = logging.getLogger(__name__)


class ModfiedModel(db.Model):
    added       = db.DateTimeProperty(required=True)
    modified    = db.DateTimeProperty(required=True)
    
    def __init__(self, *args, **kw):
        kw['added']=kw['modified']=datetime.now()
        super(ModfiedModel, self).__init__(*args, **kw)
    
    def put(self):  
        self.modified=datetime.now()
        super(ModfiedModel, self).put()

class Page(ModfiedModel):
    """ strona """
    
    slug        = db.StringProperty(verbose_name=u'slug', required=True)    
    lang        = db.StringProperty(verbose_name=u'jęyzk', required=True)
    order       = db.FloatProperty(verbose_name=u'kolejność', required=True)    
    hidden      = db.BooleanProperty(default=False)
        
    
class PageTranslation(ModfiedModel):
    """ tlumaczenie strony """
    title       = db.StringProperty(verbose_name=u'tytuł', required=True)
    content     = db.TextProperty(verbose_name=u'treść', required=True)

#    
#class PageHistory(db.Model):
#    """ historia zmian w treści strony """
#    page        = db.ReferenceProperty(PageTranslation)
#    added       = db.DateProperty(default=lambda: datetime.now())    
#
#    def __init__(self, *args, **kw):
#        kw['added']=kw['modified']=datetime.now()
#        super(Page, self).__init__(*args, **kw)
    
        
class Var(db.Model):
    """ edytowalne zmienne """        
    raw       = db.TextProperty(required=True)            
    desc      = db.StringProperty()
    
    @property
    def name(self):
        return self.key().name()
    
    @property
    def value(self):
        return yaml.load(self.raw)
    
    @classmethod
    def update_from_settings(cls):
        for name, (desc, value) in settings.VARS.iteritems():
            raw = yaml.dump(value)
            log.debug('inserting var=%s raw=%r', name, raw)  
            cls.get_or_insert(key_name=name, raw=raw, desc=desc)

    @classmethod
    def get_value(cls, name):
        current_request = webapp2.WSGIApplication.request
        if current_request is not None:
            if hasattr(current_request, 'vars_registry') and name in current_request.vars_registry:
                return current_request.vars_registry[name]
        
        value = memcache.get('Var-%s'%name) #@UndefinedVariable
        if value is not None:
            return value
        var = cls.get_by_key_name(name)
        if var is not None:
            value = var.value
            memcache.add('Var-%s'%name, value) #@UndefinedVariable        
            return value
        
        desc, value = settings.VARS[name] #@UnusedVariable
        memcache.add('Var-%s'%name, value) #@UndefinedVariable
        
        if current_request is not None:
            if not hasattr(current_request, 'vars_registry'):
                current_request.vars_registry = {}
            current_request.vars_registry[name]=value            
        return value
    
    @classmethod
    def set_value(cls, name, value):
        var = Var.get_by_key_name(name)
        assert var is not None, 'var=%s not found'%name
        expected_type = yaml.load(var.raw)
        if type(value) != type(expected_type):
            raise ValueError('expected type=%s but got=%s'%(expected_type, type(value)))
        var.raw = yaml.dump(value)
        var.put() 
        memcache.set('Var-%s'%name, value) #@UndefinedVariable
    
    def __repr__(self):
        return u'<Var(%s:%r)>'%(self.name, self.value)
            
class Image(db.Model):
    """ obrazki """
    title       = db.StringProperty(required=True)
    desc        = db.StringProperty()
    body        = db.BlobProperty(required=True) 
    
    
        


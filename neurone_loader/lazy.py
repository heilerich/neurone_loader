# This file is part of neurone_loader
# (https://www.github.com/heilerich/neurone_loader)
# Copyright © 2018 Felix Heilmeyer.
#
# This code is released under the MIT License
# http://opensource.org/licenses/mit-license.php
# Please see the file LICENSE for details.

import logging
from functools import update_wrapper, wraps

logger = logging.getLogger(__name__)

class lazy(property):
    def __init__(self, method, fget=None, fset=None, fdel=None, doc=None):
        self.method = method
        self.private_name = "_{}".format(self.method.__name__)
        doc = doc or method.__doc__
        super(lazy, self).__init__(fget=fget, fset=fset, fdel=fdel, doc=doc)
        update_wrapper(self, method)

    def __get__(self, instance, owner):
        if instance is None:
            return self
        if hasattr(instance, self.private_name):
            result = getattr(instance, self.private_name)
        else:
            logger.debug('(Lazy) loading {}.{}'.format(owner.__name__,self.method.__name__))
            if self.fget is not None:
                result = self.fget(instance)
            else:
                result = self.method(instance)
            setattr(instance, self.private_name, result)
        return result

    def __set__(self, instance, value):
        if instance is None:
            raise AttributeError
        if self.fset is None:
            setattr(instance, self.private_name, value)
        else:
            self.fset(instance, value)

def preloadable(cls):
    @wraps(cls)
    def preload(self):
        obj_type = type(self)
        def try_preload_child(attr_obj):
            if hasattr(attr_obj, '_preload_lazy_properties'):
                preloadf = getattr(attr_obj, '_preload_lazy_properties')
                if callable(preloadf):
                    attr_obj._preload_lazy_properties()
                    
        for attr in [attr for attr in dir(self) if not attr.startswith('__')]:
            possible_prop = getattr(obj_type, attr, None)
            if isinstance(possible_prop, lazy):
                if not hasattr(self, possible_prop.private_name):
                    logger.debug('Preloading property {} of {}'.format(attr,self))
                    getattr(self, attr)
            
            attr_obj = getattr(self, attr)
            try:
                _ = (e for e in attr_obj) # Iterable
                for x in attr_obj:
                    try_preload_child(x)
            except TypeError:
                # not iterable
                try_preload_child(attr_obj)

                    
    cls._preload_lazy_properties = preload
    
    def wrapper(*args, **kwargs):
        if 'preload' in kwargs:
            preload = kwargs['preload']
            del kwargs['preload']
        else:
            preload = False
        obj = cls(*args, **kwargs)
        if preload:
            obj._preload_lazy_properties()
        return obj
    return wrapper
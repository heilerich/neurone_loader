# ------------------------------------------------------------------------------
#  This file (lazy.py) is part of neurone_loader                               -
#  (https://www.github.com/heilerich/neurone_loader)                           -
#  Copyright © 2018 Felix Heilmeyer.                                           -
#                                                                              -
#  This code is released under the MIT License                                 -
#  https://opensource.org/licenses/mit-license.php                             -
#  Please see the file LICENSE for details.                                    -
# ------------------------------------------------------------------------------

import logging
from functools import update_wrapper

logger = logging.getLogger(__name__)


# noinspection PyMethodOverriding
class Lazy(property):
    def __init__(self, fget=None, fset=None, fdel=None, doc=None):
        self.private_name = "_{}".format(fget.__name__)
        doc = doc or fget.__doc__
        property.__init__(self, fget=fget, fset=fset, fdel=fdel, doc=doc)
        # noinspection PyTypeChecker
        update_wrapper(self, fget)

    def __get__(self, instance, owner):
        if instance is None:
            return self
        if hasattr(instance, self.private_name):
            result = getattr(instance, self.private_name)
        else:
            logger.debug('(Lazy) loading {}.{}'.format(owner.__name__, self.fget.__name__))
            # noinspection PyArgumentList
            result = self.fget(instance)
            setattr(instance, self.private_name, result)
        return result

    def __set__(self, instance, value):
        if self.fset is None:
            setattr(instance, self.private_name, value)
        else:
            # noinspection PyArgumentList
            self.fset(instance, value)

    def __delete__(self, instance):
        if self.fdel is None:
            delattr(instance, self.private_name)
        else:
            # noinspection PyArgumentList
            self.fdel(instance)


def preloadable(cls):
    def preload(self):
        obj_type = type(self)

        def try_preload_child(obj):
            if hasattr(obj, 'preload'):
                preload_function = getattr(obj, 'preload')
                if callable(preload_function):
                    obj.preload()
                    
        for attr in [attr for attr in dir(self) if not attr.startswith('__')]:
            possible_prop = getattr(obj_type, attr, None)
            if isinstance(possible_prop, Lazy):
                if not hasattr(self, possible_prop.private_name):
                    logger.debug('Preloading property {} of {}'.format(attr, self))
                    getattr(self, attr)
            
            attr_obj = getattr(self, attr)
            try:
                _ = (e for e in attr_obj)  # Iterable
                for x in attr_obj:
                    try_preload_child(x)
            except TypeError:
                # not iterable
                try_preload_child(attr_obj)

    cls.preload = preload
    
    def wrapper(*args, **kwargs):
        if 'preload' in kwargs:
            preload_enabled = kwargs['preload']
            del kwargs['preload']
        else:
            preload_enabled = False
        obj = cls(*args, **kwargs)
        if preload_enabled:
            obj.preload()
        return obj
    return wrapper

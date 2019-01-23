# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#  This file (test_lazy.py) is part of neurone_loader                          -
#  (https://www.github.com/heilerich/neurone_loader)                           -
#  Copyright © 2019 Felix Heilmeyer.                                           -
#                                                                              -
#  This code is released under the MIT License                                 -
#  https://opensource.org/licenses/mit-license.php                             -
#  Please see the file LICENSE for details.                                    -
# ------------------------------------------------------------------------------

from unittest import TestCase

from neurone_loader.lazy import Lazy, preloadable

_test_data = 'toast'


class TestClass(object):
    @Lazy
    def lazy_property(self):
        return _test_data

    @property
    def has_private_attribute(self):
        private_attribute_name = getattr(type(self), 'lazy_property').private_name
        return hasattr(self, private_attribute_name)


class TestLazy(TestCase):
    def setUp(self):
        self.test_data = _test_data

        self.test_object = TestClass()

    def test_lazy_loading(self):
        self.assertFalse(self.test_object.has_private_attribute)

        data = self.test_object.lazy_property
        self.assertEqual(data, self.test_data)

        self.assertTrue(self.test_object.has_private_attribute)

    def test_setting_lazy_attribute(self):
        alternate_test_data = 'TOAST'
        self.assertNotEqual(alternate_test_data, self.test_data)

        self.test_object.lazy_property = alternate_test_data
        self.assertEqual(alternate_test_data, self.test_object.lazy_property)

    def test_deletion(self):
        data = self.test_object.lazy_property
        self.assertEqual(data, self.test_data)
        self.assertTrue(self.test_object.has_private_attribute)

        del self.test_object.lazy_property
        self.assertFalse(self.test_object.has_private_attribute)

        # test deletion of not yet loaded data
        del self.test_object.lazy_property

        data = self.test_object.lazy_property
        self.assertEqual(data, self.test_data)
        self.assertTrue(self.test_object.has_private_attribute)


class TestExplicitLazy(TestLazy):
    def setUp(self):
        TestLazy.setUp(self)
        test_data = self.test_data

        class ExplicitTestClass(object):
            @Lazy
            def lazy_property(self):
                return test_data

            @lazy_property.setter
            def lazy_property(self, value):
                private_name = getattr(type(self).__dict__['lazy_property'], 'private_name')
                setattr(self, private_name, value)

            @lazy_property.deleter
            def lazy_property(self):
                private_name = getattr(type(self).__dict__['lazy_property'], 'private_name')
                if hasattr(self, private_name):
                    delattr(self, private_name)

            @property
            def has_private_attribute(self):
                private_attribute_name = getattr(type(self), 'lazy_property').private_name
                return hasattr(self, private_attribute_name)

        self.test_object = ExplicitTestClass()


class TestPreloadable(TestCase):
    def setUp(self):
        @preloadable
        class PreloadableTestClass(TestClass):
            pass

        @preloadable
        class Container(TestClass):
            def __init__(self):
                self.test_class = PreloadableTestClass()
                self.test_array = [PreloadableTestClass(), PreloadableTestClass()]

            @property
            def all_private_attributes(self):
                return self.test_class.has_private_attribute and \
                       all([tc.has_private_attribute for tc in self.test_array])

            @property
            def no_private_attributes(self):
                return (not self.test_class.has_private_attribute) and \
                       all([not tc.has_private_attribute for tc in self.test_array])

        self.test_class = Container

    def test_preload_on_init(self):
        # noinspection PyArgumentList
        test_obj = self.test_class(preload=True)
        self.assertTrue(test_obj.all_private_attributes)

    def test_manual_preload(self):
        test_obj = self.test_class()
        self.assertTrue(test_obj.no_private_attributes)
        test_obj.preload()
        self.assertTrue(test_obj.all_private_attributes)

    def test_disabled_preload(self):
        # noinspection PyArgumentList
        test_obj = self.test_class(preload=False)
        self.assertTrue(test_obj.no_private_attributes)

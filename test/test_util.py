# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#  This file (test_util.py) is part of neurone_loader                          -
#  (https://www.github.com/heilerich/neurone_loader)                           -
#  Copyright © 2019 Felix Heilmeyer.                                           -
#                                                                              -
#  This code is released under the MIT License                                 -
#  https://opensource.org/licenses/mit-license.php                             -
#  Please see the file LICENSE for details.                                    -
# ------------------------------------------------------------------------------

from unittest import TestCase
from neurone_loader.util import doc_inherit


class Parent(object):
    def func_with_doc(self):
        """
        This is the docstring
        """
        return True


class Child(Parent):
    @doc_inherit
    def func_with_doc(self):
        super(Child, self).func_with_doc()
        return False


class TestDocInheritance(TestCase):
    def test_inheritance(self):
        self.assertEqual(Parent.func_with_doc.__doc__, Child.func_with_doc.__doc__)
        child, parent = Child(), Parent()
        self.assertEqual(child.func_with_doc.__doc__, parent.func_with_doc.__doc__)
        self.assertNotEqual(child.func_with_doc(), parent.func_with_doc())
        self.assertNotEqual(Child.func_with_doc(child), Parent.func_with_doc(parent))

    def test_inherit_nothing(self):
        with self.assertRaises(NameError):
            class SecondChild(Parent):
                @doc_inherit
                def parent_does_not_have_this(self):
                    pass

            self.assertIsNone(SecondChild.parent_does_not_have_this.__doc__)

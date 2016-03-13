# -*- coding: utf-8 -*-


"""
Provides the AccountingNone singleton

AccountingNone is a null value that dissolves in basic arithmetic operations,
as illustrated in the examples below

>>> 1 + 1
2
>>> 1 + AccountingNone
1
>>> AccountingNone + 1
1
>>> AccountingNone + None
AccountingNone
>>> +AccountingNone
AccountingNone
>>> -AccountingNone
AccountingNone
>>> -(AccountingNone)
AccountingNone
>>> AccountingNone - 1
-1
>>> 1 - AccountingNone
1
>>> AccountingNone - None
AccountingNone
>>> AccountingNone / 2
0.0
>>> 2 / AccountingNone
Traceback (most recent call last):
 ...
ZeroDivisionError
>>> AccountingNone / AccountingNone
AccountingNone
>>> AccountingNone // 2
0.0
>>> 2 // AccountingNone
Traceback (most recent call last):
 ...
ZeroDivisionError
>>> AccountingNone // AccountingNone
AccountingNone
>>> AccountingNone * 2
0.0
>>> 2 * AccountingNone
0.0
>>> AccountingNone * AccountingNone
AccountingNone
>>> AccountingNone * None
AccountingNone
"""


class AccountingNoneType(object):

    def __add__(self, other):
        if other is None:
            return AccountingNone
        return other

    __radd__ = __add__

    def __sub__(self, other):
        if other is None:
            return AccountingNone
        return -other

    def __rsub__(self, other):
        if other is None:
            return AccountingNone
        return other

    def __iadd__(self, other):
        if other is None:
            return AccountingNone
        return other

    def __isub__(self, other):
        if other is None:
            return AccountingNone
        return -other

    def __pos__(self):
        return self

    def __neg__(self):
        return self

    def __floordiv__(self, other):
        """
        Overload of the // operator
        """
        if other is AccountingNone:
            return AccountingNone
        return 0.0

    def __rfloordiv__(self, other):
        raise ZeroDivisionError

    def __truediv__(self, other):
        """
        Overload of the / operator
        """
        if other is AccountingNone:
            return AccountingNone
        return 0.0

    def __rtruediv__(self, other):
        raise ZeroDivisionError

    def __mul__(self, other):
        if other is None or other is AccountingNone:
            return AccountingNone
        return 0.0

    def __rmul__(self, other):
        if other is None or other is AccountingNone:
            return AccountingNone
        return 0.0

    def __repr__(self):
        return 'AccountingNone'

    def __unicode__(self):
        return ''


AccountingNone = AccountingNoneType()


if __name__ == '__main__':
    import doctest
    doctest.testmod()

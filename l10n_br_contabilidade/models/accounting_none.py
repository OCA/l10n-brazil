# -*- coding: utf-8 -*-
# © 2016 Thomas Binsfeld
# © 2016 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
"""
Provides the AccountingNone singleton.

AccountingNone is a null value that dissolves in basic arithmetic operations,
as illustrated in the examples below. In comparisons, AccountingNone behaves
the same as zero.

>>> 1 + 1
2
>>> 1 + AccountingNone
1
>>> AccountingNone + 1
1
>>> AccountingNone + None
AccountingNone
>>> None + AccountingNone
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
>>> abs(AccountingNone)
AccountingNone
>>> AccountingNone - None
AccountingNone
>>> None - AccountingNone
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
>>> None * AccountingNone
AccountingNone
>>> str(AccountingNone)
''
>>> bool(AccountingNone)
False
>>> AccountingNone > 0
False
>>> AccountingNone < 0
False
>>> AccountingNone < 1
True
>>> AccountingNone > 1
False
>>> 0 < AccountingNone
False
>>> 0 > AccountingNone
False
>>> 1 < AccountingNone
False
>>> 1 > AccountingNone
True
>>> AccountingNone == 0
True
>>> AccountingNone == 0.0
True
>>> AccountingNone == None
True
"""

__all__ = ['AccountingNone']


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

    def __abs__(self):
        return self

    def __pos__(self):
        return self

    def __neg__(self):
        return self

    def __div__(self, other):
        if other is AccountingNone:
            return AccountingNone
        return 0.0

    def __rdiv__(self, other):
        raise ZeroDivisionError

    def __floordiv__(self, other):
        if other is AccountingNone:
            return AccountingNone
        return 0.0

    def __rfloordiv__(self, other):
        raise ZeroDivisionError

    def __truediv__(self, other):
        if other is AccountingNone:
            return AccountingNone
        return 0.0

    def __rtruediv__(self, other):
        raise ZeroDivisionError

    def __mul__(self, other):
        if other is None or other is AccountingNone:
            return AccountingNone
        return 0.0

    __rmul__ = __mul__

    def __repr__(self):
        return 'AccountingNone'

    def __str__(self):
        return ''

    def __nonzero__(self):
        return False

    def __bool__(self):
        return False

    def __eq__(self, other):
        return other == 0 or other is None or other is AccountingNone

    def __lt__(self, other):
        return 0 < other

    def __gt__(self, other):
        return 0 > other


AccountingNone = AccountingNoneType()


if __name__ == '__main__':
    import doctest
    doctest.testmod()

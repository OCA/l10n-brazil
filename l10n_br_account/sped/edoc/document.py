# -*- coding: utf-8 -*-
###############################################################################
#                                                                             #
# Copyright (C) 2015 - Luis Felipe Mileo - www.kmee.com.br                    #
#                                                                             #
# This program is free software: you can redistribute it and/or modify        #
# it under the terms of the GNU Affero General Public License as published by #
# the Free Software Foundation, either version 3 of the License, or           #
# (at your option) any later version.                                         #
#                                                                             #
# This program is distributed in the hope that it will be useful,             #
# but WITHOUT ANY WARRANTY; without even the implied warranty of              #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the               #
# GNU Affero General Public License for more details.                         #
#                                                                             #
# You should have received a copy of the GNU Affero General Public License    #
# along with this program.  If not, see <http://www.gnu.org/licenses/>.       #
###############################################################################


class ElectronicDocument(object):
    def __init__(self, edoc_list, edoc_name, *args, **kwargs):
        self.edoc_name = edoc_name
        self.edoc_list = edoc_list
        self.support_multi_send = False
        # The result as a list of row. One row per line of data in the file,
        # but not the commission one!
        self.result_row_list = None
        # The edoc buffer on which to work on
        self.edoc_buffer = None

    @classmethod
    def edoc_type(cls, edoc_name):
        """Override this method for every new parser, so that
        new_bank_statement_parser can return the good class from his name.
        """
        return False

    def _check(self, *args, **kwargs):
        """Implement a method in your edoc to pre-check it before it been
        transmitted, raise an user warning with errors for eg:
        >>> strError = ''
        >>> if self.edoc.partner_id:
        >>>     strError += "Partner not defined"
        >>> if strError:
        >>>     raise Warning(
        >>>     _('Error !'), ("Error Validating My E-Doc:\n '%s'") % (
        >>>                    strError,))
        """
        return True

    def _serializer(self, *args, **kwargs):
        """

        """
        return True

    def _send(self, *args, **kwargs):
        """
        """
        for edoc in self.edoc_list:
            edoc.write({'state': 'transmited'})
        self.result_row_list = True

    def validate(self, *args, **kwargs):
        """
        """
        return False

    def transmit(self, *args, **kwargs):
        """

        """
        self._check(*args, **kwargs)
        if not self.support_multi_send:
            while self._serializer(*args, **kwargs):
                # Send edoc one at a time
                self._send(*args, **kwargs)
                self.validate(*args, **kwargs)
                yield self.result_row_list
        else:
            self._serializer(*args, **kwargs)
            # Send a list of edoc in a single transmission
            self._send(*args, **kwargs)
            self.validate(*args, **kwargs)
            yield self.result_row_list

    def report(self, *args, **kwargs):

        return NotImplementedError


def itersubclasses(cls, _seen=None):
    """
    itersubclasses(cls)

    Generator over all subclasses of a given class, in depth first order.

    >>> list(itersubclasses(int)) == [bool]
    True
    >>> class A(object): pass
    >>> class B(A): pass
    >>> class C(A): pass
    >>> class D(B,C): pass
    >>> class E(D): pass
    >>>
    >>> for cls in itersubclasses(A):
    ...     print(cls.__name__)
    B
    D
    E
    C
    >>> # get ALL (new-style) classes currently defined
    >>> [cls.__name__ for cls in itersubclasses(object)] #doctest: +ELLIPSIS
    ['type', ...'tuple', ...]
    """
    if not isinstance(cls, type):
        raise TypeError('itersubclasses must be called with '
                        'new-style classes, not %.100r' % cls)
    if _seen is None:
        _seen = set()
    try:
        subs = cls.__subclasses__()
    except TypeError:  # fails only when cls is type
        subs = cls.__subclasses__(cls)
    for sub in subs:
        if sub not in _seen:
            _seen.add(sub)
            yield sub
            for sub in itersubclasses(sub, _seen):
                yield sub


def get_edoc(edoc_list, edoc_name, *args, **kwargs):
    """Return an instance of edoc.

    :param profile: browse_record of invoice.
    :return: class instance for given edoc import type.
    """
    for cls in itersubclasses(ElectronicDocument):
        if cls.edoc_type(edoc_name):
            return cls(edoc_list, edoc_name, *args, **kwargs)
    return ValueError

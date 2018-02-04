# -*- coding: utf-8 -*-
# Copyright 2016-2018 ACSONE SA/NV (<http://acsone.eu>)
# Copyright 2016 Akretion (<http://akretion.com>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


class DataError(Exception):

    def __init__(self, name, msg):
        super(DataError, self).__init__()
        self.name = name
        self.msg = msg

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, repr(self.name))


class NameDataError(DataError):
    pass

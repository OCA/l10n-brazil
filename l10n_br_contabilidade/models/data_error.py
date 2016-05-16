# -*- coding: utf-8 -*-
# © 2016 ACSONE SA/NV (<http://acsone.eu>)
# © 2016 Akretion (<http://akretion.com>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


class DataError(Exception):

    def __init__(self, name, msg):
        self.name = name
        self.msg = msg


class NameDataError(DataError):
    pass

# -*- coding: utf-8 -*-
# Copyright (C) 200(  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from ..document import NFe200
from ..document import NFe310


def nfe_export(cr, uid, ids, nfe_environment='1',
               nfe_version='2.00', context=None):

    if nfe_version == '3.10':
        NFe = NFe310()
    else:
        NFe = NFe200()

    nfes = NFe.get_xml(cr, uid, ids, nfe_environment, context)

    return nfes

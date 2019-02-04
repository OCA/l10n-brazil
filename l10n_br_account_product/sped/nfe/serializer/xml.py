# -*- coding: utf-8 -*-
# Copyright (C) 200(  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from ..document import NFe200
from ..document import NFe310
from ..document import NFe400


def nfe_export(invoices,
               nfe_environment='1',
               nfe_version='4.00'):

    if nfe_version == '4.00':
        NFe = NFe400()
    elif nfe_version == '3.10':
        NFe = NFe310()
    else:
        NFe = NFe200()

    nfes = NFe.get_xml(invoices,
                       nfe_environment)

    return nfes

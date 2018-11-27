# -*- coding: utf-8 -*-
# Copyright (C) 2013  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields

from .l10n_br_account_product import (
    NFE_IND_IE_DEST,
    NFE_IND_IE_DEST_DEFAULT
)


class L10nBrAccountPartnerFiscalType(models.Model):
    _inherit = 'l10n_br_account.partner.fiscal.type'

    ind_ie_dest = fields.Selection(
        selection=NFE_IND_IE_DEST,
        string=u'Contribuinte do ICMS',
        required=True,
        default=NFE_IND_IE_DEST_DEFAULT)

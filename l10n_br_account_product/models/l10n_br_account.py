# -*- coding: utf-8 -*-
# Copyright (C) 2013  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import models, fields

from .l10n_br_account_product import (
    PRODUCT_FISCAL_TYPE,
    PRODUCT_FISCAL_TYPE_DEFAULT,
    NFE_IND_IE_DEST,
    NFE_IND_IE_DEST_DEFAULT
)


class L10nBrAccountFiscalCategory(models.Model):
    _inherit = 'l10n_br_account.fiscal.category'

    fiscal_type = fields.Selection(
        PRODUCT_FISCAL_TYPE, 'Tipo Fiscal', required=True,
        default=PRODUCT_FISCAL_TYPE_DEFAULT)


class L10nBrAccountDocumentSerie(models.Model):
    _inherit = 'l10n_br_account.document.serie'

    fiscal_type = fields.Selection(
        PRODUCT_FISCAL_TYPE, 'Tipo Fiscal', required=True,
        default=PRODUCT_FISCAL_TYPE_DEFAULT)


class L10nBrAccountPartnerFiscalType(models.Model):
    _inherit = 'l10n_br_account.partner.fiscal.type'

    ind_ie_dest = fields.Selection(
        NFE_IND_IE_DEST,
        u'Contribuinte do ICMS',
        required=True,
        default=NFE_IND_IE_DEST_DEFAULT
    )

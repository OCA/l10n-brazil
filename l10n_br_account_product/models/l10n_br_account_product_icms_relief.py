# -*- coding: utf-8 -*-
# Copyright (C) 2013  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields


class L10nBrIcmsRelief(models.Model):

    _name = 'l10n_br_account_product.icms_relief'
    _description = 'Icms Relief'

    code = fields.Char(
        string=u'Código',
        size=2,
        required=True)

    name = fields.Char(
        string=u'Nome',
        size=256,
        required=True)

    active = fields.Boolean(
        string=u'Ativo',
        default=True)

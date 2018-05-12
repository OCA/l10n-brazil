# -*- coding: utf-8 -*-
# Copyright (C) 2009 - TODAY Renato Lima - Akretion
# Copyright (C) 2014  KMEE - www.kmee.com.br
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields


class L10nBrAccountFiscalDocument(models.Model):
    _name = 'l10n_br_account.fiscal.document'
    _description = 'Tipo de Documento Fiscal'

    code = fields.Char(
        string=u'Codigo',
        size=8,
        required=True)

    name = fields.Char(
        string=u'Descrição',
        size=64)

    electronic = fields.Boolean(
        string=u'Eletrônico')

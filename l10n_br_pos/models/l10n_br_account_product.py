# -*- coding: utf-8 -*-
# © 2016 KMEE INFORMATICA LTDA (https://kmee.com.br)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import fields, models


class L10nbrAccountCFOP(models.Model):
    """CFOP - Código Fiscal de Operações e Prestações"""
    _inherit = 'l10n_br_account_product.cfop'

    is_pos = fields.Boolean(
        string=u"Permitida no POS",
        help=u"Marque esta selaçao para que a cfop possa ser utililizada no "\
             u"NFC-E/SAT"
    )

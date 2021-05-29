# -*- coding: utf-8 -*-
# © 2016 KMEE INFORMATICA LTDA (https://kmee.com.br)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models

DOCUMENT_TYPE = [
    ('nf', 'NF'),
    ('nfe', 'NF-e'),
    ('cte', 'CT-e'),
    ('nfrural', 'NF Produtor'),
    ('cf', 'Cupom Fiscal'),
    ('sat', 'CF-e/SAT')
]


class CFOP(models.Model):
    """CFOP - Código Fiscal de Operações e Prestações"""
    _inherit = 'l10n_br_fiscal.cfop'

    is_pos = fields.Boolean(
        string=u"Permitida no POS",
        help=u"Marque esta seleção para que a CFOP possa ser utililizada no "
             u"NFC-E/SAT")

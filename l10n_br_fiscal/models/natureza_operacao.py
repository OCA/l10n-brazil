# Copyright 2019 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class NaturezaOperacao(models.Model):

    _name = 'l10n_br_fiscal.natureza.operacao'
    _inherit = 'l10n_br_fiscal.data.abstract'
    _description = 'Natureza Operacao'

    _sql_constraints = [
        ('fiscal_code_uniq', 'unique (code)',
         'Já existe uma Natureza Operação com este código!')]

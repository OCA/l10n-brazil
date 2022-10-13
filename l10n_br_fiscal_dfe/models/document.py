# Copyright 2018 KMEE INFORMATICA LTDA
# Gabriel Cardoso de Faria <gabriel.cardoso@kmee.com.br>

from odoo import fields, models


class FiscalDocument(models.Model):
    _inherit = "l10n_br_fiscal.document"

    dfe_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.dfe",
        string="DF-e Consult",
    )

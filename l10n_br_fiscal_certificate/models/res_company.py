# Copyright (C) 2013  Renato Lima - Akretion
# Copyright (C) 2020  Luis Felipe Mileo - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html


from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    certificate_ecnpj_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.certificate",
        string="E-CNPJ",
        domain="[('type', '=', 'e-cnpj')]",
    )

    certificate_nfe_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.certificate",
        string="NFe",
        domain="[('type', '=', 'nf-e')]",
    )

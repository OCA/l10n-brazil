# Copyright 2019 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models

from ..constants.nfse import NFSE_ENVIRONMENT_DEFAULT, NFSE_ENVIRONMENTS


class ResCompany(models.Model):
    _inherit = "res.company"

    provedor_nfse = fields.Selection(
        selection=[],
        string="NFSe Provider",
        default=False,
    )
    cultural_sponsor = fields.Boolean(
        default=False,
    )
    nfse_environment = fields.Selection(
        selection=NFSE_ENVIRONMENTS,
        string="NFSe Environment",
        default=NFSE_ENVIRONMENT_DEFAULT,
    )
    nfse_city_logo = fields.Binary(
        string="NFSe City Logo",
    )
    nfse_website = fields.Char(
        string="NFSe Website",
    )
    nfse_ssl_verify = fields.Boolean(
        string="NFSe SSL Verify",
        default=False,
    )
    city_taxation_code_id = fields.Many2many(
        comodel_name="l10n_br_fiscal.city.taxation.code", string="City Taxation Code"
    )

    def prepare_company_servico(self):
        return {
            "codigo_municipio": int(self.partner_id.city_id.ibge_code) or None,
        }

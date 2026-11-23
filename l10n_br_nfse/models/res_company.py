# Copyright 2019 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models

from ..constants.nfse import (
    NFSE_ENVIRONMENT_DEFAULT,
    NFSE_ENVIRONMENTS,
    OPERATION_NATURE,
    TAXATION_SPECIAL_REGIME,
)


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
    operation_nature = fields.Selection(
        selection=OPERATION_NATURE,
        default="1",
    )
    taxation_special_regime = fields.Selection(
        selection=TAXATION_SPECIAL_REGIME,
        default="1",
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
    nfse_use_city_pdf = fields.Boolean(
        string="Use City NFSe PDF",
        default=False,
    )
    nfse_import_product_id = fields.Many2one(
        comodel_name="product.product",
        string="Default NFS-e Import Product",
        domain="[('type', '=', 'service')]",
        help="Service product applied when a national NFS-e is imported.",
    )

    def _prepare_company_service(self):
        return {
            "codigo_municipio": int(self.partner_id.city_id.ibge_code) or None,
        }

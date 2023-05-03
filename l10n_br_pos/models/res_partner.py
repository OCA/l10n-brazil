# © 2016 KMEE INFORMATICA LTDA (https://kmee.com.br)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

from odoo import api, models

_logger = logging.getLogger(__name__)

try:
    from erpbrasil.base.fiscal import cnpj_cpf
except ImportError:
    _logger.error("erpbrasil.base library not installed")


class ResPartner(models.Model):
    _inherit = "res.partner"

    @api.model
    def create_from_ui(self, partner):
        if partner.get("vat") and cnpj_cpf.validar_cpf(partner["vat"]):
            partner["cnpj_cpf"] = cnpj_cpf.formata(partner["vat"])
            partner["company_type"] = "person"
        elif partner.get("vat") and cnpj_cpf.validar_cnpj(partner["vat"]):
            partner["cnpj_cpf"] = cnpj_cpf.formata(partner["vat"])
            partner["company_type"] = "company"

        if partner.get("cnpj_cpf"):
            partner.pop("vat")

        if partner.get("name"):
            partner["legal_name"] = partner["name"]

        res = super(ResPartner, self).create_from_ui(partner)
        return res

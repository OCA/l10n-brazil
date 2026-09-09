# © 2016 KMEE INFORMATICA LTDA (https://kmee.com.br)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from erpbrasil.base.fiscal import cnpj_cpf

from odoo import api, models


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

        res = super().create_from_ui(partner)
        return res

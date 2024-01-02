# © 2016 KMEE INFORMATICA LTDA (https://kmee.com.br)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from erpbrasil.base.fiscal import cnpj_cpf

from odoo import api, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    @api.model
    def create_from_ui(self, partner):
        vat = partner.get("vat")

        if vat:
            if cnpj_cpf.validar_cpf(vat) or cnpj_cpf.validar_cnpj(vat):
                partner["cnpj_cpf"] = cnpj_cpf.formata(vat)
                partner["company_type"] = (
                    "person" if cnpj_cpf.validar_cpf(vat) else "company"
                )

        if "vat" in partner:
            partner.pop("vat")

        if "name" in partner:
            partner["legal_name"] = partner["name"]

        return super().create_from_ui(partner)

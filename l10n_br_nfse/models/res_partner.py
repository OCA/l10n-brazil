# Copyright 2020 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from erpbrasil.base import misc

from odoo import models


class ResPartner(models.Model):

    _inherit = "res.partner"

    def prepare_partner_tomador(self, company_id):
        if self.is_company:
            tomador_cnpj = misc.punctuation_rm(self.cnpj_cpf or "")
            tomador_cpf = None
        else:
            tomador_cnpj = None
            tomador_cpf = misc.punctuation_rm(self.cnpj_cpf or "")
        partner_cep = misc.punctuation_rm(self.zip)

        if self.country_id.id != company_id:
            address_invoice_state_code = "EX"
            address_invoice_city_code = int("9999999")
            address_invoice_city_description = "EX Description"
        else:
            address_invoice_state_code = self.state_id.code
            address_invoice_city_code = int(self.city_id.ibge_code)
            address_invoice_city_description = self.city_id.name

        if self.email:
            email = self.email
        else:
            email = None

        return {
            "cnpj": tomador_cnpj,
            "cpf": tomador_cpf,
            "email": email,
            "inscricao_municipal": misc.punctuation_rm(self.inscr_mun or "") or None,
            "inscricao_estadual": misc.punctuation_rm(self.inscr_est or "") or None,
            "razao_social": str(self.legal_name[:60] or ""),
            "endereco": str(self.street or self.street_name or ""),
            "numero": self.street_number or "",
            "bairro": str(self.district or "Sem Bairro"),
            "codigo_municipio": address_invoice_city_code,
            "descricao_municipio": address_invoice_city_description,
            "uf": address_invoice_state_code,
            "municipio": self.city or None,
            "cep": int(partner_cep),
        }

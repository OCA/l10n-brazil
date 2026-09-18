from odoo import models


class PosSession(models.Model):

    _inherit = "pos.session"
#carrega pro js os dados da empresa, patch necessário nessa versão do Odoo16
    def _loader_params_res_partner(self):

        result = super()._loader_params_res_partner()

        result["search_params"]["fields"].append("is_anonymous_consumer")

        result["search_params"]["fields"] += [
            "cnpj_cpf",
            "inscr_est",
            "legal_name",
            "street_name",
            "street_number",
            "district",
            "city_id",
            "zip",
        ]

        return result

#carrega pro js os dados da empresa, patch necessário nessa versão do Odoo16
    def _loader_params_res_company(self):
        result = super()._loader_params_res_company()

        result["search_params"]["fields"] += [
            "cnpj_cpf",
            "inscr_est",
            "legal_name",
            "street_name",
            "street_number",
            "district",
            "city_id",
            "zip",
        ]

        return result

    # patch para resolver o erro Element qTrib...
    def _loader_params_uom_uom(self):

        result = super()._loader_params_uom_uom()

        result["search_params"]["fields"].append("code")

        return result
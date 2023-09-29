# Copyright 2022 KMEE - Luis Felipe Mileo
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import api, models


class SerproWebserviceCRM(models.AbstractModel):
    _inherit = "l10n_br_cnpj_search.webservice.abstract"

    @api.model
    def _serpro_import_data(self, data):
        res = super()._serpro_import_data(data)
        keys_to_remove = ["email", "legal_nature", "equity_capital"]
        for key in keys_to_remove:
            res.pop(key, None)
        return res

    @api.model
    def _import_additional_info(self, data, schema):
        if schema not in ["empresa", "qsa"]:
            return {}

        partners = data.get("socios")
        child_ids = []
        for partner in partners:
            partner_name = self.get_data(partner, "nome", title=True)
            partner_qualification = self._get_qualification(partner)

            values = {"name": partner_name, "function": partner_qualification}

            if schema == "empresa":
                partner_cpf = self.get_data(partner, "cpf")
                values.update({"cnpj_cpf": partner_cpf})

            partner_id = self.env["res.partner"].create(values).id
            child_ids.append(partner_id)

        return {
            "child_ids": [(6, 0, child_ids)],
        }

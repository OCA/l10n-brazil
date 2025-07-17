from erpbrasil.base.misc import punctuation_rm

from odoo import Command, models


class PartnerCnpjSearchWizard(models.TransientModel):
    _inherit = "partner.search.wizard"

    def default_get(self, fields):
        res = super().default_get(fields)
        active_model = self.env.context.get("active_model")
        lead_id = self.env.context.get("default_lead_id")
        if active_model == "crm.lead":
            if "currency_id" in res:
                lead_model = self.env["crm.lead"]
                lead = lead_model.browse(lead_id)
                cnpj_cpf = punctuation_rm(lead.cnpj_cpf)
                values = self._get_partner_values(cnpj_cpf)
                res.update(values)
        return res

    def action_update_partner(self):
        active_model = self.env.context.get("active_model")
        lead_id = self.env.context.get("default_lead_id")
        if active_model == "crm.lead":
            lead_model = self.env["crm.lead"]
            lead_id = lead_model.browse(lead_id)
            lead_id.partner_id.cnpj_cpf = lead_id.cnpj
            values_to_update = {
                "partner_name": self.name,
                "legal_name": self.legal_name,
                "l10n_br_ie_code": self.l10n_br_ie_code,
                "zip": self.zip,
                "street_name": self.street_name,
                "street_number": self.street_number,
                "street2": self.street2,
                "district": self.district,
                "state_id": self.state_id.id,
                "city_id": self.city_id.id,
                "country_id": self.country_id.id,
                "phone": self.phone,
                "mobile": self.mobile,
                "email_from": self.email,
                "legal_nature_id": self.legal_nature_id.id,
                "equity_capital": self.equity_capital,
                "cnae_main_id": self.cnae_main_id.id,
                "cnae_secondary_ids": [Command.set(self.cnae_secondary_ids.ids)]
                if self.cnae_secondary_ids
                else False,
            }
            lead_id.write({k: v for k, v in values_to_update.items() if v})
        return super().action_update_partner()

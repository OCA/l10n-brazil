from erpbrasil.base import misc
from erpbrasil.base.misc import punctuation_rm

from odoo import models


class PartnerCnpjSearchWizard(models.TransientModel):
    _inherit = "partner.search.wizard"

    def default_get(self, fields):
        res = super().default_get(fields)
        lead_id = self.env.context.get("default_lead_id")
        if lead_id:
            if "currency_id" in res:
                lead_model = self.env["crm.lead"]
                lead = lead_model.browse(lead_id)
                cnpj_cpf = punctuation_rm(lead.cnpj_cpf)
                misc.punctuation_rm(self.zip)
                values = self._get_partner_values(cnpj_cpf)
                res.update(values)
        return res

    def action_update_partner(self):
        if self.env.context.get("default_partner_id"):
            values_to_update = {
                "legal_name": self.legal_name,
                "name": self.name,
                "inscr_est": self.inscr_est,
                "zip": self.zip,
                "street_name": self.street_name,
                "street_number": self.street_number,
                "street2": self.street2,
                "district": self.district,
                "state_id": self.state_id.id,
                "city_id": self.city_id.id,
                "city": self.city_id.name,
                "country_id": self.country_id.id,
                "phone": self.phone,
                "mobile": self.mobile,
                "email": self.email,
                "legal_nature": self.legal_nature,
                "equity_capital": self.equity_capital,
                "cnae_main_id": self.cnae_main_id.id,
                "company_type": "company",
            }
            if self.cnae_secondary_ids:
                values_to_update["cnae_secondary_ids"] = [
                    (6, 0, self.cnae_secondary_ids.ids)
                ]
            if self.child_ids:
                values_to_update["child_ids"] = [(6, 0, self.child_ids.ids)]
            non_empty_values = {
                key: value for key, value in values_to_update.items() if value
            }
            if non_empty_values:
                self.partner_id.write(non_empty_values)

        elif self.env.context.get("default_lead_id"):
            values_to_update_lead = {
                "name": self.name,
                "partner_name": self.name,
                "legal_name": self.legal_name,
                "inscr_est": self.inscr_est,
                "zip": self.zip,
                "street": self.street_name,
                "street_number": self.street_number,
                "street2": self.street2,
                "district": self.district,
                "state_id": self.state_id.id,
                "city_id": self.city_id.id,
                "city": self.city_id.name,
                "country_id": self.country_id.id,
                "phone": self.phone,
                "mobile": self.mobile,
                "email_from": self.email,
                "legal_nature": self.legal_nature,
                "equity_capital": self.equity_capital,
                "cnae_main_id": self.cnae_main_id,
                "cnae_secondary_ids": self.cnae_secondary_ids,
            }
            non_empty_values_lead = {
                key: value for key, value in values_to_update_lead.items() if value
            }
            if non_empty_values_lead:
                crm_lead_id = self.env.context.get("default_lead_id")
                if crm_lead_id:
                    lead = self.env["crm.lead"].browse(crm_lead_id)
                    lead.write(non_empty_values_lead)

        return {"type": "ir.actions.act_window_close"}

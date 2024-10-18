from odoo import models


class PartyMixin(models.AbstractModel):
    _inherit = "l10n_br_base.party.mixin"

    def action_open_cnpj_search_wizard(self):
        res = super().action_open_cnpj_search_wizard()
        if self._name == "crm.lead":
            default_lead_id = self.id
        else:
            default_lead_id = False
        res["context"].update({"default_lead_id": default_lead_id})
        return res

from erpbrasil.base.misc import punctuation_rm

from odoo import Command, fields, models


class Lead(models.Model):
    _inherit = "crm.lead"

    cnae_secondary_ids = fields.Many2many(
        comodel_name="l10n_br_fiscal.cnae",
        relation="crm_lead_fiscal_cnae_rel",
        column1="lead_id",
        column2="cnae_id",
    )

    def _prepare_customer_values(self, partner_name, parent_id=False):
        self.ensure_one()
        values = super()._prepare_customer_values(partner_name, parent_id)
        # A lead with a CNPJ describes a company (l10n_br_crm): the company
        # data found by the CNPJ search goes to the partner as well.
        if len(punctuation_rm(self.vat or "")) == 14:
            values.update(
                {
                    "legal_nature_id": self.legal_nature_id.id,
                    "equity_capital": self.equity_capital,
                    "cnae_main_id": self.cnae_main_id.id,
                    "cnae_secondary_ids": [Command.set(self.cnae_secondary_ids.ids)],
                }
            )
        return values

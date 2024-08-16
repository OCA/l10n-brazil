from odoo import fields, models


class Lead(models.Model):
    _inherit = "crm.lead"

    cnpj_cpf = fields.Char(related="cnpj")

    cnae_secondary_ids = fields.Many2many(
        comodel_name="l10n_br_fiscal.cnae",
        relation="crm_lead_fiscal_cnae_rel",
        column1="lead_id",
        column2="cnae_id",
    )

    def _prepare_customer_values(self, name, is_company, parent_id=False):
        self.ensure_one()
        values = super()._prepare_customer_values(name, is_company, parent_id)
        values.update(
            {
                "legal_name": self.legal_name if is_company else self.name_surname,
                "street_name": self.street,
                "street_number": self.street_number,
                "district": self.district,
                "city_id": self.city_id.id,
            }
        )
        if is_company:
            values.update(
                {
                    "cnpj_cpf": self.cnpj,
                    "inscr_est": self.inscr_est,
                    "inscr_mun": self.inscr_mun,
                    "suframa": self.suframa,
                    "legal_nature": self.legal_nature,
                    "equity_capital": self.equity_capital,
                    "cnae_main_id": self.cnae_main_id.id,
                    "cnae_secondary_ids": [(6, 0, self.cnae_secondary_ids.ids)],
                }
            )
        else:
            values.update(
                {
                    "cnpj_cpf": self.cpf,
                    "inscr_est": self.rg,
                    "rg": self.rg,
                }
            )
        return values

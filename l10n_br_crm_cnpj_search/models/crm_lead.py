from odoo import Command, fields, models


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
                    "l10n_br_ie_code": self.l10n_br_ie_code,
                    "l10n_br_im_code": self.l10n_br_im_code,
                    "l10n_br_isuf_code": self.l10n_br_isuf_code,
                    "legal_nature_id": self.legal_nature_id.id,
                    "equity_capital": self.equity_capital,
                    "cnae_main_id": self.cnae_main_id.id,
                    "cnae_secondary_ids": [Command.set(self.cnae_secondary_ids.ids)],
                }
            )
        else:
            values.update(
                {
                    "cnpj_cpf": self.cpf,
                    "l10n_br_ie_code": self.l10n_br_rg_code,
                    "l10n_br_rg_code": self.l10n_br_rg_code,
                }
            )
        return values

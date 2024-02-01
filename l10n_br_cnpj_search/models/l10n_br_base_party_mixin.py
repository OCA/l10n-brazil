# Copyright 2022 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
# Copyright (C) 2024-Today - Engenere (<https://engenere.one>).
# @author Cristiano Mafra Junior

from odoo import _, api, models
from odoo.exceptions import UserError


class PartyMixin(models.AbstractModel):
    _inherit = "l10n_br_base.party.mixin"

    def action_open_cnpj_search_wizard(self):
        if not self.cnpj_cpf:
            raise UserError(_("Please enter your CNPJ"))
        if self.cnpj_validation_disabled():
            raise UserError(
                _(
                    "It is necessary to activate the option to validate de CNPJ to use"
                    " this functionality."
                )
            )
        if self._name == "res.partner":
            default_partner_id = self.id
        else:
            default_partner_id = self.partner_id.id

        return {
            "name": "Search Data by CNPJ",
            "type": "ir.actions.act_window",
            "res_model": "partner.search.wizard",
            "view_type": "form",
            "view_mode": "form",
            "context": {
                "default_partner_id": default_partner_id,
            },
            "target": "new",
        }

    @api.model
    def cnpj_validation_disabled(self):
        cnpj_validation_disabled = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("l10n_br_base.disable_cpf_cnpj_validation")
        )
        return cnpj_validation_disabled

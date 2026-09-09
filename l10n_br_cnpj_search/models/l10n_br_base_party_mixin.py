# Copyright 2022 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
# Copyright (C) 2024-Today - Engenere (<https://engenere.one>).
# @author Cristiano Mafra Junior

from odoo import api, fields, models
from odoo.exceptions import UserError

CNPJ_BRANCH_TYPE_SELECTION = [
    ("head_office", "Head Office"),
    ("branch", "Branch"),
]


class PartyMixin(models.AbstractModel):
    _inherit = "l10n_br_base.party.mixin"

    equity_capital = fields.Monetary(currency_field="br_currency_id")

    company_size = fields.Char(
        help="Company size classification (e.g. Small Business).",
    )

    cnpj_status = fields.Char(
        string="CNPJ Status",
        help="Registration status of the CNPJ (e.g. Active).",
    )

    cnpj_status_date = fields.Date(
        string="CNPJ Status Date",
        help="Date of the current registration status.",
    )

    cnpj_status_reason = fields.Char(
        string="CNPJ Status Reason",
        help="Reason for the current registration status.",
    )

    opening_date = fields.Date(
        help="Date the company started its activities.",
    )

    cnpj_branch_type = fields.Selection(
        selection=CNPJ_BRANCH_TYPE_SELECTION,
        string="Head Office / Branch",
        help="Whether the establishment is the head office or a branch.",
    )

    simples_option_date = fields.Date(
        string="Simples Nacional Option Date",
        help="Date the company opted for the Simples Nacional regime.",
    )

    legal_responsible_name = fields.Char(
        string="Legal Responsible",
        help="Name of the legal responsible for the company.",
    )

    legal_responsible_function = fields.Char(
        help="Function of the legal responsible for the company.",
    )

    cnae_main_id = fields.Many2one(comodel_name="l10n_br_fiscal.cnae")

    legal_nature_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.legal.nature",
        string="Legal Nature",
    )

    br_currency_id = fields.Many2one(
        comodel_name="res.currency",
        default=lambda self: self.env.ref("base.BRL"),
        string="BR Company Currency",
        readonly=True,
    )

    def action_open_cnpj_search_wizard(self):
        if not self.vat:
            raise UserError(self.env._("Please enter your CNPJ"))
        if self.cnpj_validation_disabled():
            raise UserError(
                self.env._(
                    "It is necessary to activate the option to validate de CNPJ to use"
                    " this functionality."
                )
            )
        context = {
            "active_model": self._name,
        }
        if self._name == "res.partner":
            context["default_partner_id"] = self.id
        elif self._name == "crm.lead":
            context["default_lead_id"] = self.id
        else:
            context["default_partner_id"] = self.partner_id.id

        return {
            "name": "Search Data by CNPJ",
            "type": "ir.actions.act_window",
            "res_model": "partner.search.wizard",
            "view_type": "form",
            "view_mode": "form",
            "context": context,
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

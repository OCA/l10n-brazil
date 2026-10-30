# Copyright (C) 2026 - TODAY, Kaynnan Lemes <kaynnan.lemes@escodoo.com.br>
# Copyright 2026 - TODAY, Cristiano Mafra Junior <cristiano.mafra@escodoo.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from datetime import timedelta

from odoo import Command, _, fields, models
from odoo.exceptions import UserError

from ..constants.duimp import DUIMP_SEARCH_DEFAULT_DAYS


class DuimpSearchWizard(models.TransientModel):
    _name = "l10n_br_duimp.search_wizard"
    _description = "Search DUIMPs available for import"

    company_id = fields.Many2one(
        comodel_name="res.company",
        required=True,
        default=lambda self: self.env.company,
    )

    date_from = fields.Date(
        required=True,
        default=lambda self: fields.Date.today()
        - timedelta(days=DUIMP_SEARCH_DEFAULT_DAYS),
    )

    date_to = fields.Date(required=True, default=fields.Date.today)

    line_ids = fields.One2many(
        comodel_name="l10n_br_duimp.search_wizard.line",
        inverse_name="wizard_id",
        string="DUIMPs Found",
    )

    def action_search_duimp(self):
        self.ensure_one()
        importer_ni = self.company_id.cnpj_cpf_stripped
        if not importer_ni:
            raise UserError(_("Please set the company CNPJ before searching!"))

        webservice = self.company_id._get_duimp_webservice()
        access_keys = webservice.search_access_keys_by_importer(
            importer_ni,
            fields.Date.to_string(self.date_from),
            fields.Date.to_string(self.date_to),
        )
        imported_numbers = set(
            self.env["l10n_br_fiscal.document"]
            .search([("duimp_number", "!=", False)])
            .mapped("duimp_number")
        )
        new_numbers = [
            access_key["numero"]
            for access_key in access_keys
            if access_key.get("numero") and access_key["numero"] not in imported_numbers
        ]
        if not new_numbers:
            if access_keys:
                raise UserError(
                    _(
                        "Every DUIMP found for this company in the selected "
                        "period has already been imported."
                    )
                )
            raise UserError(
                _(
                    "No DUIMP was found for this company in the selected "
                    "period. Try widening the date range."
                )
            )

        self.line_ids = [Command.clear()] + [
            Command.create(self._prepare_search_line_values(webservice, duimp_number))
            for duimp_number in new_numbers
        ]
        return self._reopen()

    def _prepare_search_line_values(self, webservice, duimp_number):
        general_data = webservice.get_general_data(duimp_number)
        identification = general_data.get("identificacao") or {}
        situation = general_data.get("situacao") or {}
        return {
            "wizard_id": self.id,
            "duimp_number": duimp_number,
            "duimp_version": identification.get("versao"),
            "registration_date": self.env[
                "l10n_br_duimp.declaration"
            ]._parse_payload_date(identification.get("dataRegistro")),
            "situation": situation.get("situacaoDuimp")
            or situation.get("descricaoSituacaoAtual"),
        }

    def action_import_selected(self):
        self.ensure_one()
        selected_lines = self.line_ids.filtered("selected")
        if not selected_lines:
            raise UserError(_("Select at least one DUIMP to import!"))

        declaracoes = self.env["l10n_br_duimp.declaration"]
        for line in selected_lines:
            wizard = self.env["l10n_br_fiscal.document.import.wizard"].create(
                {
                    "company_id": self.company_id.id,
                    "duimp_number": line.duimp_number,
                    "duimp_version": line.duimp_version,
                }
            )
            action = wizard.action_consult_duimp()
            declaracoes |= declaracoes.browse(action["res_id"])

        return {
            "name": _("DUIMP Imports"),
            "type": "ir.actions.act_window",
            "res_model": "l10n_br_duimp.declaration",
            "view_mode": "tree,form",
            "domain": [("id", "in", declaracoes.ids)],
            "target": "current",
        }

    def _reopen(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "view_mode": "form",
            "view_type": "form",
            "res_id": self.id,
            "views": [(False, "form")],
            "target": "new",
        }


class DuimpSearchWizardLine(models.TransientModel):
    _name = "l10n_br_duimp.search_wizard.line"
    _description = "DUIMP Search Wizard Line"

    wizard_id = fields.Many2one(
        comodel_name="l10n_br_duimp.search_wizard",
        required=True,
        ondelete="cascade",
    )

    selected = fields.Boolean(default=True)

    duimp_number = fields.Char(string="DUIMP Number", readonly=True)

    duimp_version = fields.Integer(string="Version", readonly=True)

    # Date, not Char: the payload returns a full ISO timestamp
    # ("2026-10-19T09:22:50-0300") and showing it raw is unreadable and
    # does not sort or filter as a date.
    registration_date = fields.Date(readonly=True)

    situation = fields.Char(readonly=True)

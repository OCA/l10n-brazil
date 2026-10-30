# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
import hashlib
from datetime import datetime

from odoo import _, fields, models
from odoo.exceptions import UserError

from ..constants import DEBIT_MODEL, STATUS_CANCELLED, STATUS_OPEN, STATUS_PAID

# Status code of the (simulated) DDA return layout.
CNAB_STATUS = {"1": STATUS_OPEN, "2": STATUS_PAID, "3": STATUS_CANCELLED}


class DdaImportWizard(models.TransientModel):
    """Read a DDA return file; each detail becomes a boleto, not a return event."""

    _name = "l10n_br_dda.import.wizard"
    _inherit = "cnab.import.wizard"
    _description = "Import a DDA return file (CNAB)"

    journal_id = fields.Many2one(required=False)
    cnab_structure_id = fields.Many2one(
        domain="[('is_dda_return', '=', True), ('state', '=', 'approved')]"
    )

    def _dda_vals_from_detail(self, detail):
        """Map the destination fields of the structure to the boleto fields."""
        date_text = str(detail.get("date_due") or "").strip()
        date_due = None
        if date_text and set(date_text) != {"0"}:
            try:
                date_due = datetime.strptime(date_text, "%d%m%Y").date()
            except ValueError:
                date_due = None
        guarantor_vat = str(detail.get("guarantor_vat") or "").strip()
        if not guarantor_vat.strip("0"):
            guarantor_vat = None
        status = CNAB_STATUS.get(str(detail.get("status_code") or "1").strip())
        return {
            "payer_cnpj": detail.get("payer_cnpj"),
            "digitable_line": detail.get("digitable_line"),
            "beneficiary_vat": detail.get("beneficiary_vat"),
            "beneficiary_name": detail.get("beneficiary_name"),
            "guarantor_vat": guarantor_vat,
            "guarantor_name": detail.get("guarantor_name"),
            "document_number": detail.get("document_number"),
            "amount": detail.get("amount"),
            "date_due": date_due,
            "status": status or STATUS_OPEN,
        }

    def action_import(self):
        self.ensure_one()
        if not self.return_file or not self.cnab_structure_id:
            raise UserError(_("Choose the DDA structure and the file."))
        if not self.cnab_structure_id.is_dda_return:
            raise UserError(_("The structure is not a DDA return layout."))
        if self.cnab_structure_id.cnab_format != "240":
            raise UserError(_("Only CNAB 240 DDA files are supported."))
        data = self._get_data_from_file()
        vals_list = []
        for batch in data["batches"]:
            for detail in batch["details"]:
                values = {}
                for segment in detail:
                    values.update(self._get_dict_value_from_line(segment))
                if values.get("digitable_line"):
                    vals_list.append(self._dda_vals_from_detail(values))
        digest = hashlib.sha256(base64.b64decode(self.return_file)).hexdigest()[:16]
        debits = self.env[DEBIT_MODEL]._dda_upsert(
            vals_list, "cnab", "cnab:%s" % digest
        )
        return {
            "type": "ir.actions.act_window",
            "name": _("Imported boletos"),
            "res_model": DEBIT_MODEL,
            "view_mode": "tree,form",
            "views": [[False, "tree"], [False, "form"]],
            "domain": [("id", "in", debits.ids)],
        }

    def import_cnab(self):
        return self.action_import()

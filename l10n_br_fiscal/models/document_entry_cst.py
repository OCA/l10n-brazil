# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).

from markupsafe import Markup

from odoo import _, models
from odoo.exceptions import UserError

from ..constants.fiscal import SITUACAO_EDOC_EM_DIGITACAO

ENTRY_CST_FIELDS = (
    ("entry_ipi_cst_id", "IPI"),
    ("entry_pis_cst_id", "PIS"),
    ("entry_cofins_cst_id", "COFINS"),
)


class DocumentEntryCst(models.Model):
    _inherit = "l10n_br_fiscal.document"

    def _can_recompute_entry_cst(self):
        self.ensure_one()
        return self.imported_document and self.state_edoc == SITUACAO_EDOC_EM_DIGITACAO

    def action_recompute_entry_cst(self):
        for document in self:
            if not document._can_recompute_entry_cst():
                raise UserError(
                    _(
                        "Only an imported document that is still being typed can "
                        "have its entry CST recalculated, and the document "
                        "%(document)s is not: a confirmed document is never "
                        "touched.",
                        document=document.document_number or document.display_name,
                    )
                )
            changes = []
            for index, line in enumerate(document.fiscal_line_ids, 1):
                before = {field: line[field].code for field, _label in ENTRY_CST_FIELDS}
                line._compute_entry_cst_ids()
                for field, label in ENTRY_CST_FIELDS:
                    after = line[field].code
                    if after != before[field]:
                        changes.append(
                            _(
                                "Item %(item)s, CST of the %(tax)s: %(old)s to %(new)s",
                                item=index,
                                tax=label,
                                old=before[field] or "-",
                                new=after or "-",
                            )
                        )
            if changes:
                document.message_post(
                    body=Markup("<p>%s</p><ul>%s</ul>")
                    % (
                        _("Entry CST recalculated:"),
                        Markup().join(
                            Markup("<li>%s</li>") % change for change in changes
                        ),
                    )
                )
        return True

    def action_recompute_entry_cst_selection(self):
        eligible = self.filtered(lambda document: document._can_recompute_entry_cst())
        eligible.action_recompute_entry_cst()
        skipped = len(self) - len(eligible)
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Entry CST"),
                "message": _(
                    "%(done)s document(s) recalculated, %(skipped)s left as they "
                    "are (not imported, or not in typing).",
                    done=len(eligible),
                    skipped=skipped,
                ),
                "type": "success",
                "sticky": False,
            },
        }

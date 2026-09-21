# Copyright 2026 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from odoo.addons.l10n_br_dere_spec.models.v1_2.types import FIN_EVT

from ..constants import (
    EVENT_D1001,
    EVENT_D1011,
    EVENT_D1101,
    EVENT_D1106,
    EVENT_D1121,
    EVENT_TYPES,
)
from ..models.dere_event_ops import ALLOWED_MOT_EXCL

MOT_EXCL_WAVE2 = [
    ("2", "Improper submission (inexistent fact)"),
    ("3", "Identification error (CNPJ/period)"),
    ("9", "Other"),
]


class DereEventOperationWizard(models.TransientModel):
    _name = "l10n_br_dere.event.operation.wizard"
    _description = "DeRE event replace, exclude or rectify"

    declaration_id = fields.Many2one(comodel_name="l10n_br_dere.declaration")
    table_period_id = fields.Many2one(comodel_name="l10n_br_dere.table.period")
    event_type = fields.Selection(EVENT_TYPES, required=True)
    tp_oper = fields.Selection(
        [
            ("2", "Replacement"),
            ("3", "Exclusion"),
            ("4", "Rectification after monthly closing"),
        ],
        required=True,
    )
    mot_excl = fields.Selection(MOT_EXCL_WAVE2, string="Exclusion reason")
    change_validity = fields.Boolean(string="Change table validity")
    nova_ini_valid = fields.Date(string="New validity start")
    nova_fim_valid = fields.Date(string="New validity end")
    fin_evt = fields.Selection(FIN_EVT, string="Rectification purpose")
    deduction_line_ids = fields.Many2many(
        comodel_name="l10n_br_dere.deduction.line",
        relation="dere_evt_oper_wiz_deduction_rel",
        string="Deduction documents",
    )

    @api.onchange("declaration_id")
    def _onchange_declaration_id(self):
        if self.declaration_id:
            self.deduction_line_ids = self.declaration_id.deduction_line_ids

    def action_confirm(self):
        self.ensure_one()
        extra = {}
        if self.tp_oper == "3":
            if self.mot_excl not in ALLOWED_MOT_EXCL:
                raise UserError(_("Select an exclusion reason (2, 3 or 9)."))
            extra["motExcl"] = self.mot_excl
        if self.table_period_id:
            if self.tp_oper == "2" and self.change_validity:
                if not self.nova_ini_valid:
                    raise UserError(_("Set the new validity start."))
                period = self.table_period_id
                if (
                    self.nova_ini_valid == period.ini_valid
                    and self.nova_fim_valid == period.fim_valid
                ):
                    raise UserError(
                        _(
                            "The new validity must differ from the current "
                            "table period."
                        )
                    )
                extra["novaValidade"] = {
                    "iniValid": fields.Date.to_string(self.nova_ini_valid),
                    "fimValid": fields.Date.to_string(self.nova_fim_valid)
                    if self.nova_fim_valid
                    else False,
                }
            self.table_period_id._generate_table_operation(
                tp_oper=self.tp_oper, extra=extra
            )
            return {"type": "ir.actions.act_window_close"}
        declaration = self.declaration_id
        if not declaration:
            raise UserError(_("Select a declaration or table period."))
        if self.tp_oper == "4":
            if not self.fin_evt:
                raise UserError(_("Set the D-1121 rectification purpose (finEvt)."))
            if not self.deduction_line_ids:
                raise UserError(_("Select the deduction documents to rectify."))
            extra["finEvt"] = self.fin_evt
            declaration._generate_d1121(
                tp_oper="4", extra=extra, lines=self.deduction_line_ids
            )
            return {"type": "ir.actions.act_window_close"}
        generators = {
            EVENT_D1101: declaration._generate_d1101,
            EVENT_D1106: declaration._generate_d1106,
            EVENT_D1121: declaration._generate_d1121,
            EVENT_D1001: declaration._require_table_period()._generate_d1001,
            EVENT_D1011: declaration._require_table_period()._generate_d1011,
        }
        method = generators.get(self.event_type)
        if not method:
            raise UserError(_("Unsupported event type %s.") % self.event_type)
        method(tp_oper=self.tp_oper, extra=extra)
        return {"type": "ir.actions.act_window_close"}

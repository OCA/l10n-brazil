# Copyright 2026 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models

from ..constants import EVENT_D1001, EVENT_D1011

TABLE_EVENT_TYPES = [
    (EVENT_D1001, "D-1001 Taxpayer information"),
    (EVENT_D1011, "D-1011 Commented chart of accounts"),
]


class DereTableValidity(models.Model):
    _name = "l10n_br_dere.table.validity"
    _description = "DeRE table validity in force at the RFB"
    _inherit = "dere.12.detevento"
    _order = "event_type, dere12_iniValid, id"

    company_id = fields.Many2one(
        comodel_name="res.company", required=True, index=True, readonly=True
    )
    event_type = fields.Selection(TABLE_EVENT_TYPES, required=True, readonly=True)
    event_id = fields.Many2one(
        comodel_name="l10n_br_dere.event",
        string="D-9001 source",
        ondelete="cascade",
        index=True,
        readonly=True,
        help="Table event whose D-9001 return carried this extract.",
    )
    table_period_id = fields.Many2one(
        comodel_name="l10n_br_dere.table.period",
        string="Local period",
        ondelete="set null",
        index=True,
        readonly=True,
        help="Table period whose accepted event has this receipt.",
    )


class DereTableGap(models.Model):
    _name = "l10n_br_dere.table.gap"
    _description = "DeRE table period without validity at the RFB"
    _inherit = "dere.12.detlacuna"
    _order = "event_type, dere12_iniLacuna, id"

    company_id = fields.Many2one(
        comodel_name="res.company", required=True, index=True, readonly=True
    )
    event_type = fields.Selection(TABLE_EVENT_TYPES, required=True, readonly=True)
    event_id = fields.Many2one(
        comodel_name="l10n_br_dere.event",
        string="D-9001 source",
        ondelete="cascade",
        index=True,
        readonly=True,
    )

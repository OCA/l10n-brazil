# Copyright 2026 KMEE - Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models

from ..constants import REINF_OCCURRENCE_TYPES


class ReinfOccurrence(models.Model):
    """One occurrence returned by the tax authority for a batch or an event.

    It is the regOcorrs group of the answers: the error or the warning that
    explains a rejection, kept as a record so the conference screen can list
    the reasons instead of asking the user to read a XML.
    """

    _name = "l10n_br_reinf.occurrence"
    _description = "EFD-Reinf Processing Occurrence"
    _order = "event_id, batch_id, type, id"

    event_id = fields.Many2one(
        comodel_name="l10n_br_reinf.event",
        string="Event",
        ondelete="cascade",
        index=True,
    )

    batch_id = fields.Many2one(
        comodel_name="l10n_br_reinf.batch",
        string="Batch",
        ondelete="cascade",
        index=True,
    )

    type = fields.Selection(
        selection=REINF_OCCURRENCE_TYPES,
        help="tpOcorr of the answer: an error rejects the event, a warning "
        "does not.",
    )

    code = fields.Char(
        help="codResp of the answer.",
    )

    description = fields.Char(
        help="dscResp of the answer.",
    )

    location = fields.Char(
        help="localErroAviso of the answer: where in the event the occurrence "
        "was raised.",
    )

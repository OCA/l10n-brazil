# Copyright 2022 Engenere
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class CNABLine(models.Model):

    _name = "l10n_br_cnab.line"
    _description = "Lines that make up the CNAB."

    name = fields.Char(compute="_compute_name", store=True)

    segment_name = fields.Char(
        readonly=True, states={"draft": [("readonly", "=", False)]}
    )

    sequence = fields.Integer(
        readonly=True, states={"draft": [("readonly", "=", False)]}
    )

    type = fields.Selection(
        [("header", "Header"), ("segment", "Segment"), ("trailer", "Trailer")],
        readonly=True,
        states={"draft": [("readonly", "=", False)]},
    )

    field_ids = fields.One2many(
        comodel_name="l10n_br_cnab.line.field",
        inverse_name="cnab_line_id",
        readonly=True,
        states={"draft": [("readonly", "=", False)]},
    )

    batch_id = fields.Many2one(
        comodel_name="l10n_br_cnab.batch",
        ondelete="cascade",
        readonly=True,
        states={"draft": [("readonly", "=", False)]},
    )

    cnab_file_id = fields.Many2one(
        comodel_name="l10n_br_cnab.file",
        ondelete="cascade",
        required=True,
        readonly=True,
        states={"draft": [("readonly", "=", False)]},
    )

    cnab_format = fields.Selection(related="cnab_file_id.cnab_format")

    state = fields.Selection(
        selection=[("draft", "Draft"), ("review", "Review"), ("approved", "Approved")],
        readonly=True,
        default="draft",
    )

    @api.depends("segment_name", "cnab_file_id", "cnab_file_id.name", "type")
    def _compute_name(self):
        for l in self:
            if l.type == "segment":
                name = l.segment_name
            else:
                name = l.type
            name = "%s -> %s" % (l.cnab_file_id.name, name)

            l.name = name

    def unlink(self):
        lines = self.filtered(lambda l: l.state != "draft")
        if lines:
            raise UserError(_("You cannot delete an CNAB Line which is not draft !"))
        return super(CNABLine, self).unlink()

    def check_line(self):

        cnab_fields = self.field_ids.sorted(key=lambda r: r.start_pos)

        for f in cnab_fields:
            f.check_field()

        if cnab_fields[0].start_pos != 1:
            raise UserError(
                _("%s: The start position of first field must be 1." % self.name)
            )

        ref_pos = 0
        for f in cnab_fields:
            if f.start_pos != ref_pos + 1:
                raise UserError(
                    _(
                        "%s: Start position of field '%s' is less"
                        " than the end position of the previous one."
                        % (self.name, f.name)
                    )
                )
            ref_pos = f.end_pos

        last_pos = int(self.cnab_file_id.cnab_format)
        if cnab_fields[-1].end_pos != last_pos:
            raise UserError(
                _(
                    "%s: the end position of last field is not %s."
                    % (self.name, last_pos)
                )
            )

        if self.batch_id and self.batch_id.cnab_file_id != self.cnab_file_id:
            raise UserError(
                _("%s: line cnab file is different of batch cnab file." % (self.name))
            )

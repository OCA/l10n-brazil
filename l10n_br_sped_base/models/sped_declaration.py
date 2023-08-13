# Copyright 2023 - TODAY, Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).

from lxml.builder import E

from odoo import api, fields, models


class SpedDeclaration(models.AbstractModel):
    _name = "l10n_br_sped.declaration"
    _description = "Sped Declaration"
    _inherit = ["l10n_br_sped.mixin", "mail.thread", "mail.activity.mixin"]

    @api.model
    def _get_default_dt_ini(self):
        dt = fields.Date.context_today(self)
        return dt.replace(year=dt.year - 1)

    @api.model
    def _get_default_dt_fin(self):
        dt = fields.Date.context_today(self)
        return dt.replace(year=dt.year + 1)

    # TODO display_name

    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        required=True,
        states={"done": [("readonly", True)]},
        default=lambda self: self.env.company,
    )
    state = fields.Selection(
        selection=[("draft", "Draft"), ("done", "Done")],
        readonly=True,
        tracking=True,
        copy=False,
        default="draft",
        help="State of the declaration. When the state is set to 'Done', "
        "the parameters become read-only.",
    )
    # filter = fields.Char()

    DT_INI = fields.Date(
        string="Start Date",
        default=_get_default_dt_ini,
    )

    DT_FIN = fields.Date(
        string="End Date",
        default=_get_default_dt_fin,
    )

    sped_attachment_id = fields.Many2one("ir.attachment", string="Sped Attachment")
    sped_attachment_datas = fields.Binary(
        related="sped_attachment_id.datas", string="Sped Export"
    )
    sped_attachment_name = fields.Char(
        related="sped_attachment_id.name", string="Sped Filename"
    )

    @api.model
    def _get_kind(self):
        return self._name.replace(".0000", "").split(".")[-1]

    def button_populate_sped_from_odoo(self):
        self.env["l10n_br_sped.mixin"].with_context(
            company_id=self.company_id.id,
            declaration=self,
            default_declaration_id=self.id,
        ).populate_sped_from_odoo(self._get_kind())

    def button_flush_registers(self):
        self.ensure_one()
        self.env["l10n_br_sped.mixin"].flush_registers(self._get_kind(), self.id)

    def button_create_sped_file(self):
        pass

    @api.onchange("company_id")
    def onchange_company_id(self):
        if not self.company_id:
            return
        res = self._map_from_odoo(
            self.company_id,
            None,
            None,
        )
        for k, v in res.items():
            setattr(self, k, v)

    @api.model
    def _append_view_header(self, form):
        header = E.header()
        header.append(
            E.button(
                name="button_populate_sped_from_odoo",
                type="object",
                states="draft",
                string="Pull Registers from Odoo",
                #            class="oe_highlight",
                groups="l10n_br_fiscal.group_manager",
            )
        )
        header.append(
            E.button(
                name="button_flush_registers",
                type="object",
                states="draft",
                string="Flush Registers",
                #            class="oe_highlight",
                groups="l10n_br_fiscal.group_manager",
            )
        )

        header.append(E.field(name="state", widget="statusbar"))
        form.append(header)

    @api.model
    def _append_view_footer(self, form):
        div = E.div(
            name="message_follower_ids",
        )
        div.attrib["class"] = "oe_chatter"
        div.append(E.field(name="activity_ids"))
        div.append(E.field(name="message_ids"))
        form.append(div)

    @api.model
    def _append_top_view_elements(self, group):
        group.append(E.field(name="company_id"))
        group.append(E.separator(colspan="4"))

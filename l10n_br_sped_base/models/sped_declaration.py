# Copyright 2023 - TODAY, Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).

import base64
from collections import defaultdict
from io import StringIO

from lxml.builder import E

from odoo import _, api, fields, models

from .sped_mixin import LAYOUT_VERSIONS


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

    split_sped_by_bloco = fields.Boolean()

    @api.model
    def _get_kind(self) -> str:
        return self._name.replace(".0000", "").split(".")[-1]

    def name_get(self):
        return [
            (
                declaration.id,
                f"{declaration.DT_FIN:%m-%Y}-{declaration.company_id.name.replace(' ', '_')}",
            )
            for declaration in self
        ]

    def button_populate_sped_from_odoo(self):
        """Populate SPED registers from Odoo."""
        # TODO add cron pulling from Odoo for open declarations
        log_msg = StringIO()
        log_msg.write("<h3>%s</h3>" % (_("Pulled from Odoo:"),))
        kind = self._get_kind()
        top_registers = (
            self.env["l10n_br_sped.mixin"]
            .with_context(
                company_id=self.company_id.id,
                declaration=self,
                default_declaration_id=self.id,
            )
            ._get_top_registers(kind)
        )
        for register in top_registers:
            register._pull_records_from_odoo(kind, level=2, log_msg=log_msg)

        self.message_post(body=log_msg.getvalue())

    def button_flush_registers(self):
        self.ensure_one()
        self.env["l10n_br_sped.mixin"]._flush_registers(self._get_kind(), self.id)

    def button_done(self):
        self.state = "done"

    def button_draft(self):
        self.state = "draft"

    def button_create_sped_files(self):
        """Generate and attach the SPED file."""
        self.ensure_one()
        sped_txt = self._generate_sped_text()

        if self.split_sped_by_bloco:
            attachment_vals = self._split_sped_text_by_bloco(sped_txt)
        else:
            attachment_vals = [self._create_sped_attachment(sped_txt)]
        self.env["ir.attachment"].create(attachment_vals)

    def _split_sped_text_by_bloco(self, sped_txt):
        blocos = {}
        # Split the text by bloco
        current_bloco = None
        for line in sped_txt.splitlines():
            if line.startswith(("|0", "|9")):
                continue
            current_bloco = line[1]
            if current_bloco not in blocos:
                blocos[current_bloco] = []
            if current_bloco:
                blocos[current_bloco].append(line)

        attachments_vals = []
        for bloco, lines in blocos.items():
            if len(lines) < 3:  # empty bloco
                continue
            bloco_txt = "\n".join(lines)
            attachments_vals.append(self._create_sped_attachment(bloco_txt, bloco))

        return attachments_vals

    def _create_sped_attachment(self, text, bloco=None):
        kind = self._get_kind()
        if bloco:
            file_name = f"{kind.upper()}-bloco_{bloco}-{self.name_get()[0][1]}.txt"
        else:
            file_name = f"{kind.upper()}-{self.name_get()[0][1]}.txt"

        return {
            "name": file_name,
            "res_model": self._name,
            "res_id": self.id,
            "datas": base64.b64encode(text.encode()),
            "mimetype": "application/txt",
            "type": "binary",
        }

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
        """Append custom buttons to the form view header."""
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
        header.append(
            E.button(
                name="button_done",
                type="object",
                states="draft",
                string="Set to Done",
                #            class="oe_highlight",
                groups="l10n_br_fiscal.group_manager",
            )
        )
        header.append(
            E.button(
                name="button_draft",
                type="object",
                states="done",
                string="Reset to Draft",
                #            class="oe_highlight",
                groups="l10n_br_fiscal.group_manager",
            )
        )
        header.append(
            E.button(
                name="button_create_sped_files",
                type="object",
                states="done",
                string="Generate SPED File",
                #            class="oe_highlight",
                groups="l10n_br_fiscal.group_manager",
            )
        )

        header.append(E.field(name="state", widget="statusbar"))
        form.append(header)

    @api.model
    def _append_view_footer(self, form):
        """Append the chatter elements to the form view footer."""
        div = E.div(
            name="message_follower_ids",
        )
        div.attrib["class"] = "oe_chatter"
        div.append(E.field(name="activity_ids"))
        div.append(E.field(name="message_ids"))
        form.append(div)

    @api.model
    def _append_top_view_elements(self, group, inline=False):
        """Append top-level elements to the form view."""
        group.append(E.field(name="company_id"))
        group.append(E.field(name="split_sped_by_bloco"))
        group.append(E.separator(colspan="4"))

    def _generate_sped_text(self, version=None):
        """Generate SPED text from Odoo declaration records."""
        self.ensure_one()
        kind = self._get_kind()
        if version is None:
            version = LAYOUT_VERSIONS[kind]
        top_register_classes = self._get_top_registers(kind)
        sped = StringIO()
        last_bloco = None
        line_total = 0
        # mutable register line_count https://stackoverflow.com/a/15148557
        line_count = [0]
        count_by_register = defaultdict(int)
        count_by_bloco = defaultdict(int)
        self._generate_register_text(sped, version, line_count, count_by_register)
        count_by_register["0990"] = 1  # for some reason it is needed

        for register_class in top_register_classes:
            bloco = register_class._name[-4:][0].upper()
            count_by_bloco[bloco] += register_class.search_count([])

        domain = [("declaration_id", "=", self.id)]
        for register_class in top_register_classes:
            bloco = register_class._name[-4:][0].upper()
            registers = register_class.search(domain)
            if bloco != last_bloco:
                if last_bloco:
                    sped.write(
                        "\n|%s990|%s|"
                        % (
                            last_bloco,
                            line_count[0] + 1,
                        )
                    )
                    count_by_register["%s990" % (bloco,)] = 1
                    line_total += line_count[0] + 1
                    line_count = [0]

                sped.write(
                    "\n|%s001|%s|" % (bloco, 0 if count_by_bloco[bloco] > 0 else 1)
                )
                count_by_register["%s001" % (bloco,)] = 1
                line_count[0] += 1
            registers._generate_register_text(
                sped, version, line_count, count_by_register
            )
            last_bloco = bloco

        # close the last register:
        # closing_register = "099" if kind == "ecf" else "990"
        # sped.write(f"\n|{bloco}{closing_register}|{line_count[0] + 1}|")
        sped.write(f"\n|{bloco}990|{line_count[0] + 1}|")

        # totals:
        sped.write("\n|9001|0|")
        count_by_register["9001"] = 1
        count_by_register["9990"] = 1
        count_by_register["9999"] = 1
        count_by_register["9900"] = len(count_by_register.keys()) + 1

        for item in sorted(
            count_by_register.items(), key=lambda r: self._get_alphanum_sequence(r[0])
        ):
            code = item[0]
            num = item[1]
            sped.write("\n|9900|%s|%s|" % (code, num))
        sped.write("\n|9990|%s|" % (len(count_by_register.keys()) + 3,))

        line_total += line_count[0] + len(count_by_register.keys()) + 4
        sped.write("\n|9999|%s|" % (line_total,))
        return sped.getvalue()

from collections import defaultdict
from io import StringIO

from lxml.builder import E

from odoo import api, fields, models

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
        log_msg = StringIO()
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
            register.pull_records_from_odoo(kind, level=2, log_msg=log_msg)

        self.message_post(body=log_msg.getvalue())

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

    @api.model
    def generate_sped_text(self, version=None):
        """
        Generate SPED text from Odoo declaration records.

        :param declaration: Odoo declaration record.
        :param version: SPED layout version (optional).
        :return: SPED text as a string.
        """

        self.ensure_one()
        kind = self._get_kind()
        if version is None:
            version = LAYOUT_VERSIONS[kind]
        top_register_classes = self._get_top_registers(kind)
        sped = StringIO()
        last_bloco = None
        bloco = None
        line_total = 0
        # mutable register line_count https://stackoverflow.com/a/15148557
        line_count = [0]
        count_by_register = defaultdict(int)
        count_by_bloco = defaultdict(int)
        self.generate_register_text(sped, version, line_count, count_by_register)
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
            registers.generate_register_text(
                sped, version, line_count, count_by_register
            )
            last_bloco = bloco

        # close the last register:
        if (
            kind == "ecf"
        ):  # WTF why is it different for ecf?? You kidding me? or is it an error?
            sped.write("\n|" + bloco + "099|%s|" % (line_count[0] + 1,))
        else:
            sped.write("\n|" + bloco + "990|%s|" % (line_count[0] + 1,))

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

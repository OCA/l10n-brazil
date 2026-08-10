# Copyright 2023 - TODAY, Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).

import base64
import logging
from collections import defaultdict
from io import StringIO

from lxml.builder import E

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.osv import expression

from .sped_mixin import LAYOUT_VERSIONS, SPED_ENCODING

_logger = logging.getLogger(__name__)


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

    debug = fields.Boolean(
        help=(
            "If True, will pull draft account moves and "
            "draft fiscal documents from a larger date period "
            "to help developpers develop and debug the mappings"
        )
    )

    fiscal_document_ids = fields.One2many(
        comodel_name="l10n_br_fiscal.document",
        compute="_compute_fiscal_documents",
    )

    fiscal_document_partner_ids = fields.One2many(
        comodel_name="res.partner", compute="_compute_fiscal_documents"
    )

    fiscal_document_line_ids = fields.One2many(
        comodel_name="l10n_br_fiscal.document.line", compute="_compute_fiscal_documents"
    )

    fiscal_product_ids = fields.One2many(
        comodel_name="product.product", compute="_compute_fiscal_documents"
    )

    fiscal_operation_ids = fields.One2many(
        comodel_name="l10n_br_fiscal.operation", compute="_compute_fiscal_documents"
    )

    fiscal_comment_ids = fields.One2many(
        comodel_name="l10n_br_fiscal.comment", compute="_compute_fiscal_documents"
    )

    fiscal_uom_ids = fields.One2many(
        comodel_name="uom.uom", compute="_compute_fiscal_documents"
    )

    @api.model
    def _get_kind(self) -> str:
        return self._name.replace(".0000", "").split(".")[-1]

    def name_get(self):
        return [
            (
                declaration.id,
                f"{declaration.DT_FIN:%m-%Y}-"
                f"{declaration.company_id.name.replace(' ', '_')}",
            )
            for declaration in self
        ]

    def _get_fiscal_document_period_domain(self):
        """Documents of the declaration period.

        An outgoing document belongs to the period of its emission. An entry
        belongs to the period it came in (``date_in_out``): the supplier invoice
        emitted in one month is booked in the month it was received, as an
        extemporaneous one when that is a later month. An entry without entry
        date falls back to the emission date. For an entry made from a bill,
        ``date_in_out`` is the accounting date of the bill: the real receipt
        date is not recorded in the document.

        Known limit (time zone): ``date_in_out`` of an entry made from a bill is
        the accounting date at midnight of the time zone of the user who
        launched the bill, stored in UTC (``_compute_date_in_out`` of
        l10n_br_account). A user east of UTC stores the previous day in UTC, and
        the period filter and DT_E_S read that UTC value. It is the same
        pattern as ``document_date`` (the dhEmi) and is pinned by tests of
        l10n_br_account, so it is left to the time zone audit and not changed
        here.
        """
        self.ensure_one()
        emission = [
            ("document_date", ">=", self.DT_INI),
            ("document_date", "<=", self.DT_FIN),
        ]
        entry = [
            ("date_in_out", ">=", self.DT_INI),
            ("date_in_out", "<=", self.DT_FIN),
        ]
        return expression.OR(
            [
                expression.AND([[("fiscal_operation_type", "!=", "in")], emission]),
                expression.AND([[("fiscal_operation_type", "=", "in")], entry]),
                expression.AND(
                    [
                        [
                            ("fiscal_operation_type", "=", "in"),
                            ("date_in_out", "=", False),
                        ],
                        emission,
                    ]
                ),
            ]
        )

    def _search_period_documents(self):
        """The fiscal documents of the company in the declaration period, before
        any document is left out for lack of a key (see
        ``_get_documents_without_access_key``)."""
        self.ensure_one()
        return self.env["l10n_br_fiscal.document"].search(
            [
                ("company_id", "=", self.company_id.id),
                (
                    "state_edoc",
                    "in",
                    ("autorizada", "cancelada", "denegada", "inutilizada"),
                ),
            ]
            + self._get_fiscal_document_period_domain()
        )

    def _get_documents_without_access_key(self):
        """NF-e and NFC-e (55, 65) without an access key are not a fiscal
        document the books can carry: the C100 would go out with an empty
        CHV_NFE and the PVA refuses the file. Typically a bill of a purchase
        order that has no invoice from the supplier yet. They stay out of the
        declaration and the pull lists them in the history."""
        self.ensure_one()
        if self.debug:
            return self.env["l10n_br_fiscal.document"]
        return self._search_period_documents().filtered(
            lambda doc: doc._is_sped_without_access_key()
        )

    @api.depends("company_id", "DT_INI", "DT_FIN")
    def _compute_fiscal_documents(self):
        for record in self:
            if record.debug:
                fiscal_document_ids = self.env["l10n_br_fiscal.document"].search(
                    [], order="id DESC", limit=100
                )
            else:
                fiscal_document_ids = (
                    record._search_period_documents()
                    - record._get_documents_without_access_key()
                )

            record.fiscal_document_partner_ids = fiscal_document_ids.mapped(
                "partner_id"
            )
            record.fiscal_document_line_ids = fiscal_document_ids.mapped(
                "fiscal_line_ids"
            )
            # TODO: Complementar com produtos dos outros blocos!!!!
            record.fiscal_product_ids = record.fiscal_document_line_ids.mapped(
                "product_id"
            )

            record.fiscal_document_ids = fiscal_document_ids
            record.fiscal_operation_ids = record.fiscal_document_ids.mapped(
                "fiscal_operation_id"
            )
            record.fiscal_comment_ids = record.fiscal_document_ids.mapped(
                "comment_ids"
            ) | record.fiscal_document_line_ids.mapped("comment_ids")

            # TODO: Complementar com unidades de medidas de outros blocos!!!
            record.fiscal_uom_ids = record.fiscal_document_line_ids.mapped("uom_id")

    def _in_company_context(self):
        """The declaration in the environment of its own company.

        The access rules by company hide the documents of every company that is
        not active in the session, so a declaration of the company B pulled with
        the company A active went out without documents and without a warning.
        Pulling the registers and generating the file run as the company of the
        declaration, which the user has to have access to.
        """
        self.ensure_one()
        company = self.company_id
        if not self.env.su and company not in self.env.user.company_ids:
            raise UserError(
                _(
                    "You have no access to the company %(company)s of this "
                    "declaration, so its registers cannot be pulled or its "
                    "file generated.",
                    company=company.sudo().display_name,
                )
            )
        return self.with_company(company).with_context(allowed_company_ids=company.ids)

    def button_populate_sped_from_odoo(self):
        """Populate SPED registers from Odoo."""
        # TODO add cron pulling from Odoo for open declarations
        self.ensure_one()
        self._in_company_context()._populate_sped_from_odoo()

    def _populate_sped_from_odoo(self):
        """Pull the registers from Odoo. Returns the errors of the registers that
        could not be pulled (a list of text): a register that fails is left out
        of the declaration, with a note in the history, so whoever generates the
        file has to know it is incomplete."""
        self.ensure_one()
        errors = []
        log_msg = StringIO()
        log_msg.write(f"<h3>{_('Pulled from Odoo')}</h3>")
        kind = self._get_kind()

        # The declaration record IS the 0000: without its own mapping the header
        # goes out blank and the validator refuses the file. Only empty fields are
        # written, so what the user typed wins.
        if hasattr(self, "_map_from_odoo"):
            header_record = self.company_id
            if self._odoo_model and self._odoo_model != "res.company":
                header_record = self.env[self._odoo_model].search(
                    self._odoo_domain(None, self), limit=1
                )
            vals = self._map_from_odoo(header_record, None, self)
            self.write(
                {field: value for field, value in vals.items() if not self[field]}
            )
        mixin_env = self.env["l10n_br_sped.mixin"].with_context(
            company_id=self.company_id.id,
            declaration=self,
            default_declaration_id=self.id,
        )
        top_registers = mixin_env._get_top_registers(kind)

        # pulling twice must not duplicate: drop what an earlier pull created
        mixin_env._flush_generated_registers(kind, self.id)

        ignored = self._get_documents_without_access_key()
        if ignored:
            title = _("Documents left out for lack of an access key")
            log_msg.write(
                f"<p style='color:orange;'>{title}: "
                + ", ".join(
                    f"{doc.document_type_id.code} {doc.document_serie or ''}/"
                    f"{doc.document_number or doc.id}"
                    for doc in ignored
                )
                + "</p>"
            )

        for register_model in top_registers:  # Iterate over models, not instances
            try:
                with self.env.cr.savepoint():
                    register_model._pull_records_from_odoo(
                        kind, level=2, log_msg=log_msg
                    )
            except Exception as e:
                _logger.error(
                    f"Error pulling records for {register_model._name}: {e}",
                    exc_info=True,
                )
                log_msg.write(
                    "<p style='color:red;'>Error "
                    f"processing {register_model._name}: {e}</p>"
                )
                errors.append(f"{register_model._name[-4:].upper()}: {e}")
        self.message_post(body=log_msg.getvalue())
        return errors

    def button_flush_registers(self):
        self.ensure_one()
        self.env["l10n_br_sped.mixin"]._flush_registers(self._get_kind(), self.id)
        self.message_post(
            body=f"<h3>{_('Flushed all Registers from Declaration!')}</h3>"
        )

    def button_done(self):
        self.state = "done"

    def button_draft(self):
        self.state = "draft"

    def button_create_sped_files(self):
        """Generate and attach the SPED file.

        The registers of Odoo are pulled again at every generation, so the file
        never goes out with registers that are older than the registration or
        the assessment it is made of (the pull is idempotent and keeps what was
        typed by hand). A register that cannot be pulled stops the generation
        with the reason, instead of going out missing from the file."""
        self.ensure_one()
        self._check_accountant()
        errors = self._in_company_context()._populate_sped_from_odoo()
        if errors:
            raise UserError(
                _(
                    "Some registers could not be pulled from Odoo and a file "
                    "without them is incomplete, so it was not generated. Fix "
                    "the cause and generate it again:\n%(errors)s",
                    errors="\n".join(errors),
                )
            )
        sped_txt = self._generate_sped_text()

        if self.split_sped_by_bloco:
            attachment_vals = self._split_sped_text_by_bloco(sped_txt)
        else:
            attachment_vals = [self._create_sped_attachment(sped_txt)]
        self.env["ir.attachment"].create(attachment_vals)

    def _get_accountant_required(self):
        """(field of the accountant, label) that the record 0100 of the layout
        marks as mandatory; each kind of declaration that has the record lists
        them."""
        return []

    def _check_accountant(self):
        """The record 0100 comes from the accountant of the company, and the PVA
        refuses it without the mandatory fields of the layout: say which ones
        are missing in the registration instead of leaving the record out."""
        for declaration in self:
            required = declaration._get_accountant_required()
            if declaration.debug or not required:
                continue
            accountant = declaration.company_id.accountant_id
            if not accountant:
                raise UserError(
                    _(
                        "Set the accountant of the company (Accountant field, "
                        "with CPF and CRC) before generating the file: the record "
                        "0100 comes from it."
                    )
                )
            missing = [label for field, label in required if not accountant[field]]
            if missing:
                raise UserError(
                    _(
                        "The registration of the accountant %(name)s lacks "
                        "%(missing)s, which the record 0100 of the file needs. "
                        "Fill it in the contact of the accountant.",
                        name=accountant.display_name,
                        missing=", ".join(missing),
                    )
                )

    def _split_sped_text_by_bloco(self, sped_txt):
        blocos = defaultdict(list)
        current_bloco = None
        for line in sped_txt.splitlines():
            # A register line is "|REG|...". Anything else is skipped: block
            # 0/9 summary lines, and fragments left by a field value that
            # contained a line break. This also guarantees the split can never
            # crash on a corrupted line.
            if not line.startswith("|") or len(line) < 2 or line[1] in "09":
                continue
            current_bloco = line[1]
            if current_bloco:
                blocos[current_bloco].append(line)

        attachments_vals = []
        for bloco, lines in blocos.items():
            if len(lines) < 3:  # empty bloco
                continue
            bloco_txt = "\n".join(lines)
            attachments_vals.append(self._create_sped_attachment(bloco_txt, bloco))

        return attachments_vals

    @staticmethod
    def _to_crlf(text):
        """Every line of a SPED file ends in CR LF, the last one included (the
        layout and the PVA demand it). The text is built with LF only."""
        text = text.replace("\r\n", "\n").replace("\n", "\r\n")
        return text if text.endswith("\r\n") else text + "\r\n"

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
            # SPED files are ISO-8859-1, not the utf-8 of the default
            # encode(); errors="replace" keeps a character outside Latin-1
            # pasted in some journal item label from aborting the whole
            # file generation
            "datas": base64.b64encode(
                self._to_crlf(text).encode(SPED_ENCODING, errors="replace")
            ),
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
                string=_("Pull Registers from Odoo"),
                #            class="oe_highlight",
                groups="l10n_br_fiscal.group_manager",
            )
        )
        header.append(
            E.button(
                name="button_flush_registers",
                type="object",
                states="draft",
                string=_("Flush Registers"),
                #            class="oe_highlight",
                groups="l10n_br_fiscal.group_manager",
            )
        )
        header.append(
            E.button(
                name="button_done",
                type="object",
                states="draft",
                string=_("Set to Done"),
                #            class="oe_highlight",
                groups="l10n_br_fiscal.group_manager",
            )
        )
        header.append(
            E.button(
                name="button_draft",
                type="object",
                states="done",
                string=_("Reset to Draft"),
                #            class="oe_highlight",
                groups="l10n_br_fiscal.group_manager",
            )
        )
        header.append(
            E.button(
                name="button_create_sped_files",
                type="object",
                states="done",
                string=_("Generate SPED File"),
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
        group.append(E.field(name="debug"))
        group.append(E.separator(colspan="4"))

    def _skip_empty_blocks(self):
        """Return True to omit blocks with no records (ECF rejects them)."""
        return False

    def _generate_sped_text(self, version=None):
        """Generate SPED text from Odoo declaration records."""
        self.ensure_one()
        return self._in_company_context()._generate_sped_text_in_company(version)

    def _generate_sped_text_in_company(self, version=None):
        self.ensure_one()
        kind = self._get_kind()
        if version is None:
            version = LAYOUT_VERSIONS[kind]
        top_register_classes = self._get_top_registers(kind)
        sped = StringIO()
        line_total = 0
        # mutable register line_count https://stackoverflow.com/a/15148557
        line_count = [0]
        count_by_register = defaultdict(int)
        self._generate_register_text(sped, version, line_count, count_by_register)

        # group the top registers by block, keeping the order
        blocks = []
        for register_class in top_register_classes:
            bloco = register_class._name[-4:][0].upper()
            if not blocks or blocks[-1][0] != bloco:
                blocks.append((bloco, []))
            blocks[-1][1].append(register_class)

        domain = [("declaration_id", "=", self.id)]
        skip_empty = self._skip_empty_blocks()
        first = True
        for bloco, register_classes in blocks:
            # search by this declaration only: other declarations' records
            # would open an empty block as "with data"
            records = [
                register_class.search(domain) for register_class in register_classes
            ]
            has_data = any(records)
            if skip_empty and not has_data and bloco != "0":
                continue
            if not first:
                line_count = [0]
            sped.write(f"\n|{bloco}001|{0 if has_data else 1}|")
            count_by_register[f"{bloco}001"] = 1
            line_count[0] += 1
            for record in records:
                record._generate_register_text(
                    sped, version, line_count, count_by_register
                )
            sped.write(f"\n|{bloco}990|{line_count[0] + 1}|")
            count_by_register[f"{bloco}990"] = 1
            line_total += line_count[0] + 1
            first = False

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
            sped.write(f"\n|9900|{code}|{num}|")
        block_9_lines = len(count_by_register.keys()) + 3
        sped.write(f"\n|9990|{block_9_lines}|")

        line_total += block_9_lines
        sped.write(f"\n|9999|{line_total}|")
        return sped.getvalue()

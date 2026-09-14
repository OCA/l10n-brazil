# Copyright 2026 KMEE (Ygor Carvalho <ygor.carvalho@kmee.com.br>)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import base64

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from .declaration_xml import DeclarationXmlError, parse_declaration

INTERMEDIATION = [
    ("1", "1 - Por conta propria"),
    ("2", "2 - Por conta e ordem"),
    ("3", "3 - Encomenda"),
]

TRANSPORT_VIA = [
    ("1", "1 - Maritima"),
    ("2", "2 - Fluvial"),
    ("3", "3 - Lacustre"),
    ("4", "4 - Aerea"),
    ("5", "5 - Postal"),
    ("6", "6 - Ferroviaria"),
    ("7", "7 - Rodoviaria"),
    ("8", "8 - Conduto/Rede Transmissao"),
    ("9", "9 - Meios Proprios"),
    ("10", "10 - Entrada/Saida Ficta"),
    ("11", "11 - Courier"),
    ("12", "12 - Em maos"),
    ("13", "13 - Por reboque"),
]


class ImportDeclarationAddition(models.TransientModel):
    """One addition of the declaration, with the tax it charged on its own goods.

    The addition is the unit that matters. A declaration groups the goods by
    tariff classification, and the rate changes from one group to the next: in
    the one this was written against, the Import Tax is 12,60% on one addition
    and 18,00% on the other, and the IPI is 3,25% against 9,75%. Spreading a
    single total over every line of the note by weight cannot reproduce that,
    and the note leaves with tax the declaration did not charge.
    """

    _name = "l10n_br_account.import.declaration.addition"
    _description = "Import Declaration Addition"
    _order = "number"

    wizard_id = fields.Many2one(
        comodel_name="l10n_br_account.import.declaration.wizard",
        required=True,
        ondelete="cascade",
    )
    company_currency_id = fields.Many2one(related="wizard_id.company_currency_id")
    number = fields.Char(string="Addition", required=True)
    ncm_code = fields.Char(string="NCM")
    customs_value = fields.Monetary(
        currency_field="company_currency_id",
        help="Base of the Import Tax of the addition, which is the customs "
        "value of the goods it covers.",
    )
    ii_rate = fields.Float(string="II %")
    ii_value = fields.Monetary(string="II", currency_field="company_currency_id")
    ipi_value = fields.Monetary(string="IPI", currency_field="company_currency_id")
    pis_value = fields.Monetary(string="PIS", currency_field="company_currency_id")
    cofins_value = fields.Monetary(
        string="COFINS", currency_field="company_currency_id"
    )
    manufacturer_code = fields.Char(string="Foreign Manufacturer Code")
    line_ids = fields.Many2many(
        comodel_name="account.move.line",
        # Named by hand because the one Odoo derives from the two models is
        # longer than what PostgreSQL accepts for a table.
        relation="import_declaration_addition_move_line_rel",
        column1="addition_id",
        column2="line_id",
        string="Invoice Lines",
        help="The lines of the foreign invoice this addition covers.",
    )
    unmatched = fields.Text(
        string="Goods without a line",
        readonly=True,
        help="Goods of the addition that no line of the invoice answered for.",
    )


class ImportDeclarationWizard(models.TransientModel):
    """Build the entry NF-e of an import from the bill and the declaration.

    The foreign supplier issues an invoice in its own currency, the customs
    broker registers the declaration, and only then the importer issues its own
    entry note, in BRL, to move the goods from the customs area. The values that
    note carries are the ones the declaration charged: they were paid, so they
    are the authority, not a recomputation from rates.

    This wizard takes the bill of the foreign invoice and the numbers of the
    declaration and writes the fiscal document with them.
    """

    _name = "l10n_br_account.import.declaration.wizard"
    _description = "Import Declaration to Entry NF-e"

    move_id = fields.Many2one(
        comodel_name="account.move",
        string="Foreign Invoice",
        required=True,
        help="The vendor bill of the invoice issued abroad.",
    )
    company_id = fields.Many2one(related="move_id.company_id")
    partner_id = fields.Many2one(related="move_id.partner_id")
    fiscal_operation_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.operation",
        string="Fiscal Operation",
        required=True,
        domain=[("fiscal_operation_type", "=", "in")],
    )
    fiscal_operation_line_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.operation.line",
        string="Operation Line",
        required=True,
        domain="[('fiscal_operation_id', '=', fiscal_operation_id)]",
    )
    document_type_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.document.type",
        string="Document Type",
        required=True,
    )
    document_serie_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.document.serie",
        string="Document Serie",
        domain="[('document_type_id', '=', document_type_id)]",
    )
    document_date = fields.Datetime(
        required=True,
        default=fields.Datetime.now,
    )

    customs_value = fields.Monetary(
        required=True,
        currency_field="company_currency_id",
        help="Valor aduaneiro in BRL, as converted by the declaration exchange "
        "rate. It becomes the gross amount of the note lines.",
    )
    company_currency_id = fields.Many2one(related="move_id.company_id.currency_id")

    di_file = fields.Binary(
        string="Declaration XML",
        help="The XML of the import declaration, as the Siscomex hands it out. "
        "Loading it fills the declaration and its additions.",
    )
    di_filename = fields.Char()
    addition_ids = fields.One2many(
        comodel_name="l10n_br_account.import.declaration.addition",
        inverse_name="wizard_id",
        string="Additions",
    )
    unclaimed_lines = fields.Text(
        string="Lines no addition claimed",
        readonly=True,
        help="Lines of the invoice that no addition of the declaration "
        "answered for.",
    )

    di_number = fields.Char(string="Declaration Number", required=True)
    di_date = fields.Date(string="Registration Date", required=True)
    clearance_date = fields.Date()
    clearance_place = fields.Char(required=True)
    clearance_state_id = fields.Many2one(
        comodel_name="res.country.state",
        string="Clearance State",
        required=True,
        domain=[("country_id.code", "=", "BR")],
    )
    transport_via = fields.Selection(
        selection=TRANSPORT_VIA,
        required=True,
    )
    intermediation = fields.Selection(
        selection=INTERMEDIATION,
        required=True,
        default="1",
        help="Mandatory in the schema and it comes before the exporter code, so "
        "leaving it out makes the validation blame cExportador instead.",
    )
    afrmm_value = fields.Monetary(
        string="AFRMM",
        currency_field="company_currency_id",
        help="Required by the schema when the transport is waterway.",
    )
    exporter_code = fields.Char(
        required=True,
        help="Without it the XML does not even validate, and the error message "
        "blames the next element.",
    )
    addition_number = fields.Char(default="1", required=True)
    manufacturer_code = fields.Char(string="Foreign Manufacturer Code")

    ii_value = fields.Monetary(string="II", currency_field="company_currency_id")
    ipi_value = fields.Monetary(string="IPI", currency_field="company_currency_id")
    pis_value = fields.Monetary(string="PIS", currency_field="company_currency_id")
    cofins_value = fields.Monetary(
        string="COFINS", currency_field="company_currency_id"
    )
    icms_value = fields.Monetary(string="ICMS", currency_field="company_currency_id")
    customhouse_charges = fields.Monetary(
        string="Customs Charges",
        currency_field="company_currency_id",
        help="Siscomex fee and the other charges the declaration lists.",
    )

    document_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.document",
        string="Generated Document",
        readonly=True,
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        move = self.env["account.move"].browse(res.get("move_id"))
        operation = move.fiscal_operation_id
        if (
            operation
            and operation.fiscal_operation_type == "in"
            and "fiscal_operation_id" in fields_list
            and not res.get("fiscal_operation_id")
        ):
            res["fiscal_operation_id"] = operation.id
            if operation.line_ids and "fiscal_operation_line_id" in fields_list:
                res["fiscal_operation_line_id"] = operation.line_ids[0].id
        if (
            move.document_serie_id
            and "document_serie_id" in fields_list
            and not res.get("document_serie_id")
        ):
            res["document_serie_id"] = move.document_serie_id.id
        return res

    @api.onchange("di_file")
    def _onchange_di_file(self):
        """Fill the form the moment the file is chosen.

        The button below does the same for whoever sets the file from code, but
        on the screen the onchange is what makes the values appear without the
        dialog having to be reopened.
        """
        if self.di_file:
            self._load_declaration()

    def action_load_declaration(self):
        """Fill the wizard from the XML of the declaration.

        What the operator would otherwise transcribe from the printed extract is
        thirteen fields of the header plus, for every addition, its tariff
        classification and the tax it charged. The file carries all of it, and
        it carries the goods of each addition, which is what tells the note
        which line answers to which rate.
        """
        self.ensure_one()
        if not self.di_file:
            raise UserError(_("Choose the XML of the declaration first."))
        self._load_declaration()
        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
        }

    def _load_declaration(self):
        self.ensure_one()
        content = base64.b64decode(self.di_file)
        try:
            declaration = parse_declaration(content)
        except DeclarationXmlError as error:
            raise UserError(str(error)) from error
        self.update(self._values_from_declaration(declaration))

    def _values_from_declaration(self, declaration):
        self.ensure_one()
        state = self.env["res.country.state"].search(
            [
                ("code", "=", declaration["clearance_state"]),
                ("country_id.code", "=", "BR"),
            ],
            limit=1,
        )
        prepared_additions = self._additions_from_declaration(declaration)
        values = {
            "di_number": declaration["number"],
            "di_date": declaration["registration_date"],
            "clearance_date": declaration["clearance_date"],
            "clearance_place": declaration["clearance_place"],
            "transport_via": declaration["transport_via"],
            "addition_ids": [(5, 0, 0)]
            + [(0, 0, prepared) for prepared in prepared_additions],
        }
        if prepared_additions:
            values["customs_value"] = sum(
                prepared["customs_value"] for prepared in prepared_additions
            )
            values["ii_value"] = sum(
                prepared["ii_value"] for prepared in prepared_additions
            )
            values["ipi_value"] = sum(
                prepared["ipi_value"] for prepared in prepared_additions
            )
            values["pis_value"] = sum(
                prepared["pis_value"] for prepared in prepared_additions
            )
            values["cofins_value"] = sum(
                prepared["cofins_value"] for prepared in prepared_additions
            )
        if state:
            values["clearance_state_id"] = state.id
        if declaration["customhouse_charges"] and not self.customhouse_charges:
            values["customhouse_charges"] = declaration["customhouse_charges"]
        if declaration.get("afrmm") and not self.afrmm_value:
            values["afrmm_value"] = declaration["afrmm"]
        if declaration["icms_value"] and not self.icms_value:
            values["icms_value"] = declaration["icms_value"]
        exporter = next(
            (a["exporter"] for a in declaration["additions"] if a["exporter"]), ""
        )
        if exporter and not self.exporter_code:
            values["exporter_code"] = exporter[:60]
        # The other half of what the matching learns. A line the declaration
        # never mentions and a good with no line are the two faces of an invoice
        # that disagrees with the declaration, and seeing only one of them sends
        # whoever is checking to the wrong side.
        claimed = self.env["account.move.line"]
        for prepared in values["addition_ids"][1:]:
            claimed |= claimed.browse(prepared[2]["line_ids"][0][2])
        left = self._bill_lines() - claimed
        values["unclaimed_lines"] = (
            "\n".join(
                _("%(line)s, quantity %(quantity)s")
                % {"line": line.name, "quantity": line.quantity}
                for line in left
            )
            or False
        )
        return values

    def _additions_from_declaration(self, declaration):
        """Each addition with its own numbers and the invoice lines it covers."""
        self.ensure_one()
        available = self._bill_lines()
        prepared = []
        for addition in declaration["additions"]:
            matched, unmatched = self._match_goods(addition["items"], available)
            available -= matched
            prepared.append(
                {
                    "number": addition["number"],
                    "ncm_code": addition["ncm"],
                    "customs_value": addition["customs_value"],
                    "ii_rate": addition["ii_rate"],
                    "ii_value": addition["ii_value"],
                    "ipi_value": addition["ipi_value"],
                    "pis_value": addition["pis_value"],
                    "cofins_value": addition["cofins_value"],
                    "manufacturer_code": addition["manufacturer"][:60] or False,
                    "line_ids": [(6, 0, matched.ids)],
                    "unmatched": "\n".join(unmatched) or False,
                }
            )
        return prepared

    @staticmethod
    def _comparable(text):
        return " ".join((text or "").split()).upper()

    def _match_goods(self, items, available):
        """Tie each good of the addition to the line of the invoice that carries it.

        The declaration describes the goods in its own words and the invoice
        names them by product, so what the two share is the description and the
        match is by containment. A declaration often lists the same product more
        than once, with different quantities, so where several lines answer the
        same description the quantity decides which one; without that the second
        listing would take whatever was left.

        Whatever finds no line comes back named, with its quantity. Guessing an
        addition onto the wrong line puts the wrong rate on it, and the operator
        reading `quantity 1 found no line` is usually looking at an invoice that
        disagrees with the declaration, which is worth seeing.
        """
        matched = available.browse()
        unmatched = []
        for item in items:
            description = self._comparable(item["description"])
            code = item["description"].split(" - ")[0].strip()
            candidates = available.filtered(
                lambda line, code=code, wanted=description: (
                    code and line.product_id.default_code == code
                )
                or (
                    wanted
                    and wanted in self._comparable(line.name or line.product_id.name)
                )
            )
            candidates -= matched
            if not candidates:
                unmatched.append(
                    _("%(goods)s, quantity %(quantity)s")
                    % {
                        "goods": item["description"],
                        "quantity": item["quantity"],
                    }
                )
                continue
            same_quantity = candidates.filtered(
                lambda line, wanted=item["quantity"]: abs(line.quantity - wanted)
                < 0.001
            )
            matched |= (same_quantity or candidates)[0]
        return matched, unmatched

    @api.onchange("fiscal_operation_id")
    def _onchange_fiscal_operation_id(self):
        lines = self.fiscal_operation_id.line_ids
        self.fiscal_operation_line_id = lines[:1]

    def _bill_lines(self):
        self.ensure_one()
        lines = self.move_id.invoice_line_ids.filtered(
            lambda line: line.display_type == "product"
        )
        if not lines:
            raise UserError(_("The foreign invoice has no product line."))
        return lines

    def _shares(self, lines):
        """Weight of each bill line, by its own subtotal.

        The declaration gives one customs value and one amount per tax for the
        whole shipment, so the note has to spread them over the lines. The
        weight comes from the invoice, which is the only per item information
        that exists, and the last line takes the rounding difference so the note
        closes on the declaration to the cent.
        """
        total = sum(lines.mapped("price_subtotal"))
        if not total:
            raise UserError(
                _(
                    "The foreign invoice adds up to zero, "
                    "there is no weight to split by."
                )
            )
        return [line.price_subtotal / total for line in lines]

    def _split(self, amount, shares, currency):
        parts = []
        left = amount
        for share in shares[:-1]:
            part = currency.round(amount * share)
            parts.append(part)
            left -= part
        parts.append(left)
        return parts

    def _prepare_document_values(self):
        self.ensure_one()
        return {
            "partner_id": self.partner_id.id,
            "company_id": self.company_id.id,
            "document_type_id": self.document_type_id.id,
            "document_serie_id": self.document_serie_id.id,
            "fiscal_operation_id": self.fiscal_operation_id.id,
            "document_date": self.document_date,
            "date_in_out": self.document_date,
        }

    def _prepare_line_values(self, bill_line, gross):
        self.ensure_one()
        quantity = bill_line.quantity or 1.0
        return {
            "product_id": bill_line.product_id.id,
            "fiscal_operation_id": self.fiscal_operation_id.id,
            "fiscal_operation_line_id": self.fiscal_operation_line_id.id,
            "quantity": quantity,
            "price_unit": gross / quantity,
            "uom_id": bill_line.product_uom_id.id,
        }

    @staticmethod
    def _rate(value, base):
        return (value / base * 100.0) if base else 0.0

    def _di_values(self, number=None, manufacturer=None):
        self.ensure_one()
        addition_number = str(int(number or self.addition_number))
        values = {
            "nfe40_nDI": self.di_number,
            "nfe40_dDI": self.di_date,
            "nfe40_xLocDesemb": self.clearance_place,
            "nfe40_dDesemb": self.clearance_date or self.di_date,
            "nfe40_tpViaTransp": self.transport_via,
            "nfe40_tpIntermedio": self.intermediation,
            "nfe40_cExportador": self.exporter_code,
            "state_clearance_id": self.clearance_state_id.id,
            "nfe40_adi": [
                (
                    0,
                    0,
                    {
                        "nfe40_nAdicao": addition_number,
                        "nfe40_nSeqAdic": "1",
                        "nfe40_cFabricante": manufacturer
                        or self.manufacturer_code
                        or self.exporter_code,
                    },
                )
            ],
        }
        if self.afrmm_value:
            values["nfe40_vAFRMM"] = self.afrmm_value
        return values

    def _write_declaration(self, line, number=None, manufacturer=None):
        """Attach the declaration to the line, when the NF-e module is there.

        Soft dependency: the DI fields come from the NF-e schema and live on the
        concrete fiscal document line, so they only exist when l10n_br_nfe is
        installed.
        """
        self.ensure_one()
        if "nfe40_DI" not in line._fields:
            return False
        # sudo on the spec record: the declaration is a consequence of generating
        # the note, and the access of the nfe.40 models belongs to the NF-e
        # groups, which whoever books the bill does not necessarily carry.
        declaration = (
            self.env["nfe.40.di"]
            .sudo()
            .create(self._di_values(number=number, manufacturer=manufacturer))
        )
        line.sudo().nfe40_DI = [(6, 0, declaration.ids)]
        return declaration

    def _tax_fields(self):
        """What the declaration knows and the product file cannot.

        The Import Tax it actually charged, given the classification and any
        tariff exception, and the customs charges. The rate of the IPI, of the
        contributions and of the ICMS belongs to the product and to the CFOP, so
        the engine computes those and the declaration only checks the result.
        """
        return (
            # Written twice on purpose. The declared value is what composes the
            # base of the other taxes, and the engine copies it into ii_value
            # when the line carries an Import Tax at all. A line whose product
            # file has no Import Tax has no such compute to run, and without
            # the second write the amount the declaration charged would vanish
            # from the note.
            ("ii_declared_value", self.ii_value),
            ("ii_value", self.ii_value),
        )

    def _declared_totals(self):
        """Taxes the product file owns, so the declaration only checks them.

        With the additions loaded the amount to check against is their sum, not
        what was typed in the header: the file is the record of what was paid,
        and the header fields are the manual path for whoever has no file. The
        ICMS is of the despatch and has no per addition figure, so it stays in
        the header either way.
        """
        if not self.addition_ids:
            return (
                ("ipi_value", self.ipi_value),
                ("pis_value", self.pis_value),
                ("cofins_value", self.cofins_value),
                ("icms_value", self.icms_value),
            )
        return (
            ("ipi_value", sum(self.addition_ids.mapped("ipi_value"))),
            ("pis_value", sum(self.addition_ids.mapped("pis_value"))),
            ("cofins_value", sum(self.addition_ids.mapped("cofins_value"))),
            ("icms_value", self.icms_value),
        )

    def _check_against_declaration(self, document):
        """Refuse the note when the product file and the declaration disagree.

        Finding it out here is far cheaper than through a SEFAZ rejection: 528
        when the amount does not follow the base and the rate, 538 when the
        total does not follow the items.
        """
        self.ensure_one()
        currency = self.company_currency_id
        # The declaration totals the amounts it rounded per item, and the note
        # rounds again when it spreads them over the lines, so one cent per line
        # is arithmetic and not a divergence worth refusing a note for.
        tolerance = 0.01 * max(len(document.fiscal_line_ids), 1)
        diverged = []
        for fname, declared in self._declared_totals():
            computed = sum(document.fiscal_line_ids.mapped(fname))
            if abs(computed - declared) > tolerance:
                diverged.append(
                    f"{fname}: {currency.round(computed)} from the product file, "
                    f"{currency.round(declared)} in the declaration"
                )
        if diverged:
            raise UserError(
                _(
                    "The note does not close on the declaration:\n%s\n\n"
                    "The rate of these taxes comes from the product and from "
                    "the CFOP, so a difference here is a tax mapping to fix, "
                    "not a value to force."
                )
                % "\n".join(diverged)
            )

    def _blocks(self):
        """The groups the note is built from, each with its own tax.

        With the declaration loaded, a group is an addition: its goods, its
        customs value and the tax it charged, which is the only way the rate of
        each line comes out as the declaration applied it. Without it, the whole
        invoice is one group and the totals typed by hand are spread over it,
        which is what the wizard did before the file could be read.
        """
        self.ensure_one()
        if not self.addition_ids:
            return [
                {
                    "lines": self._bill_lines(),
                    "customs_value": self.customs_value,
                    "taxes": dict(self._tax_fields()),
                    "number": self.addition_number,
                    "manufacturer": self.manufacturer_code,
                }
            ]
        blocks = []
        for addition in self.addition_ids:
            lines = addition.line_ids.filtered(
                lambda line: line.display_type == "product"
            )
            if not lines:
                raise UserError(
                    _(
                        "Addition %s has no line of the invoice answering for "
                        "it. Tie its goods to the lines before generating."
                    )
                    % addition.number
                )
            blocks.append(
                {
                    "lines": lines,
                    "customs_value": addition.customs_value,
                    "taxes": {
                        "ii_declared_value": addition.ii_value,
                        "ii_value": addition.ii_value,
                    },
                    "number": addition.number,
                    "manufacturer": addition.manufacturer_code,
                }
            )
        return blocks

    def _customhouse_charges_by_line(self, blocks):
        """The Siscomex fee and the AFRMM both ride the ICMS "por dentro"
        base as customs charges of the whole despatch — neither belongs to
        any one addition. Splitting only the Siscomex fee and leaving the
        AFRMM out of the base is what left the ICMS short on a maritime
        import: the note computed without it, the declaration charged with
        it, and the two never closed.
        """
        self.ensure_one()
        empty = self._bill_lines().browse()
        all_lines = sum((block["lines"] for block in blocks), empty)
        total_charges = self.customhouse_charges + self.afrmm_value
        if not total_charges or not all_lines:
            return {}
        shares = self._shares(all_lines)
        parts = self._split(total_charges, shares, self.company_currency_id)
        return dict(zip(all_lines.ids, parts, strict=False))

    def _write_block(self, document, block, customhouse_by_line):
        """Write the lines of one group, with the tax that belongs to it."""
        self.ensure_one()
        currency = self.company_currency_id
        lines = block["lines"]
        shares = self._shares(lines)
        gross_parts = self._split(block["customs_value"], shares, currency)
        tax_parts = {
            fname: self._split(amount, shares, currency)
            for fname, amount in block["taxes"].items()
        }
        Line = self.env["l10n_br_fiscal.document.line"]
        pairs = []
        for position, bill_line in enumerate(lines):
            # The values of the declaration were paid, so they win over any
            # recomputation from rates. ii_declared_value has to be there from
            # create(): the IPI base is composed by the same compute that
            # derives it, and writing it onto the line afterwards leaves the
            # IPI the engine already derived from the product's own Import Tax
            # rate, not the one the declaration charged.
            declared_taxes = {
                fname: parts[position]
                for fname, parts in tax_parts.items()
                if parts[position]
            }
            charge = customhouse_by_line.get(bill_line.id, 0.0)
            if charge:
                declared_taxes["ii_customhouse_charges"] = charge
            line = Line.create(
                dict(
                    self._prepare_line_values(bill_line, gross_parts[position]),
                    document_id=document.id,
                    **declared_taxes,
                )
            )
            pairs.append((bill_line, line))
            self._write_declaration(
                line, number=block["number"], manufacturer=block["manufacturer"]
            )
            # On an import CFOP the fiscal amount already adds II, PIS, COFINS,
            # ICMS and the customs charges to the untaxed amount, so the only
            # tax left outside the price is the IPI. Without writing it here the
            # document total keeps the IPI the engine computed from the product
            # rate instead of the one the declaration charged.
            values = {"amount_tax_included": 0.0}
            # The base of the IPI and of the contributions is composed by the
            # engine, which takes the Import Tax the declaration charged. The
            # ICMS is not: the engine only puts the IPI inside its base for
            # some kinds of recipient, and on an import it always belongs
            # there, so the base is grossed up here with everything in it. The
            # rate stays the one of the product file, and keeping it is what
            # makes base times rate reproduce the amount: the SEFAZ recomputes
            # that product and refuses the note with 528 otherwise.
            # Base and rate of the Import Tax follow the amount charged, so
            # base times rate reproduces it. The engine only derives them when
            # the product file carries an Import Tax of its own; on a line
            # without one there is no compute to run, and the SEFAZ recomputes
            # that product and refuses the note with 528 when it does not close.
            gross = gross_parts[position]
            declared = declared_taxes.get("ii_declared_value", 0.0)
            if declared:
                values["ii_base"] = gross
                values["ii_percent"] = self._rate(declared, gross)
            before_icms = (
                gross
                + declared_taxes.get("ii_declared_value", 0.0)
                + declared_taxes.get("ii_customhouse_charges", 0.0)
                + line.ipi_value
                + line.pis_value
                + line.cofins_value
            )
            rate = line.icms_percent or 0.0
            if rate:
                icms_base = before_icms / (1 - rate / 100.0)
                values["icms_base"] = icms_base
                values["icms_value"] = icms_base * rate / 100.0
            values["other_value"] = (
                line.pis_value
                + line.cofins_value
                + declared_taxes.get("ii_customhouse_charges", 0.0)
            )
            if declared:
                vprod_gross = gross + declared
                # freight_value and insurance_value are added back on top of
                # vProd by _add_fields_to_amount, so they have to come out of
                # the unit price here — otherwise the note's total counts the
                # customs value's own freight and insurance twice.
                vprod_gross -= line.freight_value + line.insurance_value
                values["price_unit"] = vprod_gross / line.quantity
                values["ipi_base"] = line.ipi_base
                values["ipi_percent"] = line.ipi_percent
                values["ipi_value"] = line.ipi_value
                values["pis_base"] = line.pis_base
                values["pis_percent"] = line.pis_percent
                values["pis_value"] = line.pis_value
                values["cofins_base"] = line.cofins_base
                values["cofins_percent"] = line.cofins_percent
                values["cofins_value"] = line.cofins_value
            # II sits inside vProd, PIS/COFINS inside vOutro and ICMS inside
            # its own grossed base: the fiscal total already carries them all,
            # and each one still gets its own tax line in the accounting. They
            # have to be declared as included, or the goods line books them a
            # second time and the payable overshoots the note. IBS/CBS are
            # only stated in 2026, not charged, so they come out the same way.
            values["amount_tax_included"] = (
                declared
                + values.get("icms_value", line.icms_value)
                + line.pis_value
                + line.cofins_value
                + line.ibs_value
                + line.cbs_value
            )
            line.write(values)
        return pairs

    def action_generate_document(self):
        """Write the entry note from the bill and the declaration."""
        self.ensure_one()
        if self.document_id:
            raise UserError(
                _("This wizard already generated the document %s.")
                % self.document_id.display_name
            )
        shadow_document = self.move_id.fiscal_document_id
        document = self.env["l10n_br_fiscal.document"].create(
            self._prepare_document_values()
        )
        blocks = self._blocks()
        customhouse_by_line = self._customhouse_charges_by_line(blocks)
        pairs = []
        for block in blocks:
            pairs.extend(self._write_block(document, block, customhouse_by_line))

        document.invalidate_recordset()
        self._check_against_declaration(document)
        # The values are the declaration's now, not the product file's. Marking
        # the document as imported freezes them against any later recompute and
        # makes the accounting book them as-is, the way an imported NF-e is.
        # Only then can each bill line adopt its new fiscal line: the move line
        # delegates its fiscal fields to it, and adopting it before the freeze
        # let the bill line's own onchange chain rewrite the line from the
        # product's rate.
        document.imported_document = True
        for bill_line, line in pairs:
            bill_line.fiscal_document_line_id = line
        self.document_id = document
        self.move_id.fiscal_document_id = document
        if shadow_document and shadow_document.state_edoc == "em_digitacao":
            shadow_document.action_document_cancel()
        return {
            "name": _("Import Entry Note"),
            "type": "ir.actions.act_window",
            "res_model": "l10n_br_fiscal.document",
            "view_mode": "form",
            "res_id": document.id,
        }

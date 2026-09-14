# Copyright 2026 KMEE (Ygor Carvalho <ygor.carvalho@kmee.com.br>)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import _, api, fields, models
from odoo.exceptions import UserError

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
        string="Document Date",
        required=True,
        default=fields.Datetime.now,
    )

    customs_value = fields.Monetary(
        string="Customs Value",
        required=True,
        currency_field="company_currency_id",
        help="Valor aduaneiro in BRL, as converted by the declaration exchange "
        "rate. It becomes the gross amount of the note lines.",
    )
    company_currency_id = fields.Many2one(related="move_id.company_id.currency_id")

    di_number = fields.Char(string="Declaration Number", required=True)
    di_date = fields.Date(string="Registration Date", required=True)
    clearance_date = fields.Date(string="Clearance Date")
    clearance_place = fields.Char(string="Clearance Place", required=True)
    clearance_state_id = fields.Many2one(
        comodel_name="res.country.state",
        string="Clearance State",
        required=True,
        domain=[("country_id.code", "=", "BR")],
    )
    transport_via = fields.Selection(
        selection=TRANSPORT_VIA,
        string="Transport Via",
        required=True,
    )
    intermediation = fields.Selection(
        selection=INTERMEDIATION,
        string="Intermediation",
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
        string="Exporter Code",
        required=True,
        help="Without it the XML does not even validate, and the error message "
        "blames the next element.",
    )
    addition_number = fields.Char(string="Addition Number", default="1", required=True)
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

    def _di_values(self):
        self.ensure_one()
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
                        "nfe40_nAdicao": self.addition_number,
                        "nfe40_nSeqAdic": "1",
                        "nfe40_cFabricante": self.manufacturer_code
                        or self.exporter_code,
                    },
                )
            ],
        }
        if self.afrmm_value:
            values["nfe40_vAFRMM"] = self.afrmm_value
        return values

    def _write_declaration(self, line):
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
        declaration = self.env["nfe.40.di"].sudo().create(self._di_values())
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
            ("ii_value", self.ii_value),
            ("ii_customhouse_charges", self.customhouse_charges),
        )

    def _declared_totals(self):
        """Taxes the product file owns, so the declaration only checks them."""
        return (
            ("ipi_value", self.ipi_value),
            ("pis_value", self.pis_value),
            ("cofins_value", self.cofins_value),
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

    @staticmethod
    def _rate(value, base):
        return (value / base * 100.0) if base else 0.0

    def action_generate_document(self):
        """Write the entry note from the bill and the declaration."""
        self.ensure_one()
        if self.document_id:
            raise UserError(
                _("This wizard already generated the document %s.")
                % self.document_id.display_name
            )
        bill_lines = self._bill_lines()
        shares = self._shares(bill_lines)
        currency = self.company_currency_id

        document = self.env["l10n_br_fiscal.document"].create(
            self._prepare_document_values()
        )
        gross_parts = self._split(self.customs_value, shares, currency)
        tax_parts = {
            fname: self._split(amount, shares, currency)
            for fname, amount in self._tax_fields()
        }

        Line = self.env["l10n_br_fiscal.document.line"]
        for position, bill_line in enumerate(bill_lines):
            line = Line.create(
                dict(
                    self._prepare_line_values(bill_line, gross_parts[position]),
                    document_id=document.id,
                )
            )
            self._write_declaration(line)
            # The values of the declaration were paid, so they win over any
            # recomputation from rates. These fields are stored computes with
            # readonly=False, which is what makes writing them stick.
            values = {
                fname: parts[position]
                for fname, parts in tax_parts.items()
                if parts[position]
            }
            # On an import CFOP the fiscal amount already adds II, PIS, COFINS,
            # ICMS and the customs charges to the untaxed amount, so the only
            # tax left outside the price is the IPI. Without writing it here the
            # document total keeps the IPI the engine computed from the product
            # rate instead of the one the declaration charged.
            values["amount_tax_included"] = 0.0
            # The Import Tax follows the customs value, and its rate comes out of
            # the division so base times rate reproduces the amount charged. The
            # SEFAZ recomputes it and refuses with 528 when they disagree.
            gross = gross_parts[position]
            values["ii_base"] = gross
            values["ii_percent"] = self._rate(values.get("ii_value", 0.0), gross)
            # The ICMS of an import is charged on the note total with itself
            # inside, so its base is everything else grossed up by the rate. The
            # engine cannot compose that base on its own because it uses the
            # Import Tax of the product rate instead of the one the declaration
            # charged, but the rate is cadastro, and keeping it is what makes
            # base times rate reproduce the amount: the SEFAZ recomputes it and
            # refuses the note with 528 otherwise.
            rate = line.icms_percent or 0.0
            if rate:
                before_icms = (
                    gross
                    + values.get("ii_value", 0.0)
                    + values.get("ii_customhouse_charges", 0.0)
                    + line.ipi_value
                    + line.pis_value
                    + line.cofins_value
                )
                icms_base = before_icms / (1 - rate / 100.0)
                values["icms_base"] = icms_base
                values["icms_value"] = icms_base * rate / 100.0
            line.write(values)

        document.invalidate_recordset()
        self._check_against_declaration(document)
        self.document_id = document
        return {
            "name": _("Import Entry Note"),
            "type": "ir.actions.act_window",
            "res_model": "l10n_br_fiscal.document",
            "view_mode": "form",
            "res_id": document.id,
        }

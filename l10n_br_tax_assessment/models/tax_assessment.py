# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import _, api, fields, models
from odoo.exceptions import UserError

# Sign convention of the breakdown. OCA's `account_tax_balance` already returns
# the balance with the sign flipped (`-balance`), so an outbound tax (an
# accounting credit) comes out POSITIVE. We keep that convention: a debit in the
# running account is tax owed on sales, a credit is tax recoverable on
# purchases.
KIND_DEBIT = "debit"
KIND_CREDIT = "credit"
KIND_DEDUCTION = "deduction"
KIND_WITHHOLDING = "withholding"
KIND_SPECIAL_DEBIT = "special_debit"


class TaxAssessment(models.Model):
    """Consumption tax assessment for a period.

    This is a BATCH, following the same pattern as the other period routines:
    it has a state, a persisted breakdown, validation and a final artefact (the
    closing journal entry).

    Why it exists: EFD ICMS/IPI block E and EFD Contribuicoes block M are
    OUTPUTS of an assessment, not computations of their own. Without this layer
    every tax book recomputes from scratch and the numbers match neither each
    other nor the accounting. With it, the tax books only serialize what has
    already been assessed and reviewed.

    The totals published here follow, one by one, the structure of EFD ICMS/IPI
    record E110, which is the offsetting the law defines. That is deliberate: it
    is what lets the record merely read, with no arithmetic of its own.
    """

    _name = "l10n_br_tax.assessment"
    _description = "Apuração de Imposto sobre Consumo"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "date_to desc, tax_group_id"

    name = fields.Char(compute="_compute_name", store=True)
    company_id = fields.Many2one(
        comodel_name="res.company",
        required=True,
        default=lambda self: self.env.company,
        states={"draft": [("readonly", False)]},
        readonly=True,
    )
    tax_group_id = fields.Many2one(
        comodel_name="account.tax.group",
        string="Grupo de imposto",
        required=True,
        states={"draft": [("readonly", False)]},
        readonly=True,
        help="Grupo apurado nesta conta gráfica (ICMS, IPI, PIS, COFINS). "
        "As contas contábeis usadas no encerramento vêm deste grupo "
        "(property_tax_payable_account_id e irmãs), que o core já modela.",
    )
    tax_domain = fields.Selection(
        related="tax_group_id.fiscal_tax_group_id.tax_domain",
        store=True,
        readonly=True,
        help="Tributo brasileiro do grupo. É por aqui que a escrituração acha "
        "a apuração que deve serializar: o bloco E procura icms, o bloco M "
        "procura pis e cofins.",
    )
    regime = fields.Selection(
        related="tax_group_id.regime",
        store=True,
        readonly=True,
        help="Regime apurado, herdado do grupo de imposto (critério de "
        "partição: um grupo por regime, então uma apuração nunca mistura "
        "regimes nem conta a mesma linha duas vezes). PIS e COFINS têm "
        "apuração separada por regime, como o M200 da EFD Contribuições "
        "pede; ICMS e IPI usam 'Não se aplica'.\n"
        "O campo é armazenado porque entra na chave única do período, e o "
        "grupo o declara obrigatório: um regime nulo faria a chave deixar "
        "de valer, porque no Postgres NULL nunca é igual a NULL.",
    )
    date_from = fields.Date(
        string="De",
        required=True,
        states={"draft": [("readonly", False)]},
        readonly=True,
    )
    date_to = fields.Date(
        string="Até",
        required=True,
        states={"draft": [("readonly", False)]},
        readonly=True,
    )
    state = fields.Selection(
        selection=[
            ("draft", "Rascunho"),
            ("computed", "Apurada"),
            ("posted", "Encerrada"),
            ("cancel", "Cancelada"),
        ],
        default="draft",
        required=True,
        tracking=True,
    )
    line_ids = fields.One2many(
        comodel_name="l10n_br_tax.assessment.line",
        inverse_name="assessment_id",
        string="Memória de cálculo",
        readonly=True,
    )
    move_id = fields.Many2one(
        comodel_name="account.move",
        string="Lançamento de encerramento",
        readonly=True,
        copy=False,
    )

    previous_assessment_id = fields.Many2one(
        comodel_name="l10n_br_tax.assessment",
        string="Apuração anterior",
        readonly=True,
        help="Apuração imediatamente anterior do mesmo grupo e empresa. É de "
        "onde vem o saldo credor transportado.",
    )
    previous_balance = fields.Monetary(
        string="Saldo credor anterior",
        readonly=True,
        help="Saldo credor transportado do período anterior. Positivo quando "
        "há crédito a aproveitar. É o campo 10 do E110.",
    )

    # Totals in E110 order. See `_compute_totals` for the formula.
    debit_total = fields.Monetary(
        string="Débitos (saídas)",
        compute="_compute_totals",
        store=True,
        help="Campo 02 do E110: débitos por saídas com débito do imposto.",
    )
    adjustment_debit_total = fields.Monetary(
        string="Ajustes a débito",
        compute="_compute_totals",
        store=True,
        help="Campo 04 do E110.",
    )
    credit_reversal_total = fields.Monetary(
        string="Estornos de crédito",
        compute="_compute_totals",
        store=True,
        help="Campo 05 do E110.",
    )
    credit_total = fields.Monetary(
        string="Créditos (entradas)",
        compute="_compute_totals",
        store=True,
        help="Campo 06 do E110: créditos por entradas com crédito do imposto.",
    )
    adjustment_credit_total = fields.Monetary(
        string="Ajustes a crédito",
        compute="_compute_totals",
        store=True,
        help="Campo 08 do E110.",
    )
    debit_reversal_total = fields.Monetary(
        string="Estornos de débito",
        compute="_compute_totals",
        store=True,
        help="Campo 09 do E110.",
    )
    balance = fields.Monetary(
        string="Saldo do período",
        compute="_compute_totals",
        store=True,
        help="Todo o lado devedor menos todo o lado credor, já descontado o "
        "saldo credor anterior. Positivo = saldo devedor apurado; "
        "negativo = saldo credor a transportar.",
    )
    assessed_balance = fields.Monetary(
        string="Saldo devedor apurado",
        compute="_compute_totals",
        store=True,
        help="Campo 11 do E110: o saldo do período quando devedor, zero "
        "quando credor.",
    )
    deduction_total = fields.Monetary(
        string="Deduções",
        compute="_compute_totals",
        store=True,
        help="Campo 12 do E110. Abate o saldo devedor já apurado, e por isso "
        "não entra no confronto de débitos com créditos.",
    )
    amount_payable = fields.Monetary(
        string="A recolher",
        compute="_compute_totals",
        store=True,
        help="Campo 13 do E110: saldo devedor apurado menos deduções.",
    )
    amount_carried_forward = fields.Monetary(
        string="Saldo credor a transportar",
        compute="_compute_totals",
        store=True,
        help="Campo 14 do E110.",
    )
    withholding_total = fields.Monetary(
        string="Retenção na fonte",
        compute="_compute_totals",
        store=True,
        help="Retido na fonte e deduzido no período. Abate o saldo devedor "
        "já apurado, igual à dedução, mas em campo próprio.",
    )
    special_debit_total = fields.Monetary(
        string="Débito especial",
        compute="_compute_totals",
        store=True,
        help="Campo 15 do E110: recolhido ou a recolher extra-apuração. Não "
        "altera o saldo do período.",
    )
    currency_id = fields.Many2one(
        related="company_id.currency_id", string="Moeda", readonly=True
    )

    _sql_constraints = [
        (
            "unique_period_group_company",
            "unique(company_id, tax_group_id, regime, date_from, date_to)",
            "Já existe uma apuração deste grupo de imposto, regime e "
            "período nesta empresa.",
        ),
    ]

    @api.constrains("date_from", "date_to")
    def _check_period(self):
        for record in self:
            if record.date_to < record.date_from:
                raise UserError(
                    _("A data final da apuração é anterior à data inicial.")
                )

    @api.depends("tax_group_id", "date_from", "date_to")
    def _compute_name(self):
        for record in self:
            if not record.tax_group_id or not record.date_from:
                record.name = _("Nova apuração")
                continue
            record.name = "{} {}".format(
                record.tax_group_id.name,
                record.date_from.strftime("%m/%Y"),
            )

    @api.depends(
        "line_ids.tax_amount",
        "line_ids.kind",
        "line_ids.source",
        "line_ids.adjustment_kind",
        "previous_balance",
    )
    def _compute_totals(self):
        """Reproduce the E110 offsetting, field by field.

        What separates a "debit adjustment" from a "credit reversal", and both
        from a "debit on sales", is only the ORIGIN of the line: assessed from
        move lines, or a manual adjustment carrying a table 5.1.1 code. They add
        to the same side, but the tax authority wants to see them apart.
        """
        for record in self:
            totals = dict.fromkeys(
                (
                    "debit",
                    "adjustment_debit",
                    "credit_reversal",
                    "credit",
                    "adjustment_credit",
                    "debit_reversal",
                    "deduction",
                    "withholding",
                    "special_debit",
                ),
                0.0,
            )
            for line in record.line_ids:
                totals[record._total_key_for_line(line)] += line.tax_amount

            record.debit_total = totals["debit"]
            record.adjustment_debit_total = totals["adjustment_debit"]
            record.credit_reversal_total = totals["credit_reversal"]
            record.credit_total = totals["credit"]
            record.adjustment_credit_total = totals["adjustment_credit"]
            record.debit_reversal_total = totals["debit_reversal"]
            record.deduction_total = totals["deduction"]
            record.withholding_total = totals["withholding"]
            record.special_debit_total = totals["special_debit"]

            debit_side = (
                totals["debit"] + totals["adjustment_debit"] + totals["credit_reversal"]
            )
            credit_side = (
                totals["credit"]
                + totals["adjustment_credit"]
                + totals["debit_reversal"]
                + record.previous_balance
            )
            balance = debit_side - credit_side
            record.balance = balance
            # One of the two is always zero: either there is tax due, or there
            # is a credit balance to carry over to the next period.
            record.assessed_balance = balance if balance > 0 else 0.0
            record.amount_carried_forward = -balance if balance < 0 else 0.0
            # A deduction only offsets what was already assessed as due: it
            # never creates a credit balance nor a negative amount payable.
            record.amount_payable = max(
                record.assessed_balance - totals["deduction"] - totals["withholding"],
                0.0,
            )

    @api.model
    def _total_key_for_line(self, line):
        """Which E110 total the line adds to.

        An assessed line always lands in the plain total (fields 02 and 06). A
        manual line lands in the matching adjustment field, and the table 5.1.1
        code refines between a plain adjustment and a reversal.
        """
        if line.kind in (KIND_DEDUCTION, KIND_WITHHOLDING):
            return line.kind
        if line.kind == KIND_SPECIAL_DEBIT:
            return "special_debit"
        if line.source != "manual":
            return line.kind
        if line.adjustment_kind == "credit_reversal":
            return "credit_reversal"
        if line.adjustment_kind == "debit_reversal":
            return "debit_reversal"
        return "adjustment_debit" if line.kind == KIND_DEBIT else "adjustment_credit"

    # ------------------------------------------------------------------
    # Apuracao
    # ------------------------------------------------------------------

    def _get_period_context(self):
        """The context OCA's `account_tax_balance` expects.

        Reusing that module is deliberate: it already knows how to read balance
        and base per tax over a period, telling regular apart from refund,
        straight from the move lines. The assessment READS from it rather than
        recomputing.
        """
        self.ensure_one()
        return {
            "from_date": self.date_from,
            "to_date": self.date_to,
            "company_id": self.company_id.id,
            "company_ids": [self.company_id.id],
            "target_move": "posted",
        }

    def _get_taxes(self):
        """Taxes of the assessed group, within the assessment company."""
        self.ensure_one()
        return self.env["account.tax"].search(
            [
                ("tax_group_id", "=", self.tax_group_id.id),
                ("company_id", "=", self.company_id.id),
            ]
        )

    def _find_previous_assessment(self):
        self.ensure_one()
        return self.search(
            [
                ("company_id", "=", self.company_id.id),
                ("tax_group_id", "=", self.tax_group_id.id),
                ("regime", "=", self.regime),
                ("date_to", "<", self.date_from),
                ("state", "in", ("computed", "posted")),
            ],
            order="date_to desc",
            limit=1,
        )

    def action_compute(self):
        """Build the period breakdown from the move lines."""
        for record in self:
            if record.state not in ("draft", "computed"):
                raise UserError(
                    _("Só é possível apurar uma apuração em rascunho ou já apurada.")
                )
            record.line_ids.filtered(lambda line: line.source == "computed").unlink()

            previous = record._find_previous_assessment()
            record.previous_assessment_id = previous
            record.previous_balance = previous.amount_carried_forward

            taxes = record._get_taxes().with_context(**record._get_period_context())
            vals_list = []
            for tax in taxes:
                # `type_tax_use` decides the side of the running account: a
                # sale tax is a debit (owed) and a purchase tax is a credit
                # (recoverable). `account_tax_balance` returns both with a
                # positive sign, so the classification is ours to make.
                if tax.type_tax_use == "sale":
                    kind = KIND_DEBIT
                elif tax.type_tax_use == "purchase":
                    kind = KIND_CREDIT
                else:
                    continue
                if not tax.balance and not tax.base_balance:
                    continue
                vals_list.append(
                    {
                        "assessment_id": record.id,
                        "tax_id": tax.id,
                        "kind": kind,
                        "base_amount": tax.base_balance,
                        "tax_amount": tax.balance,
                        "source": "computed",
                    }
                )
            if vals_list:
                self.env["l10n_br_tax.assessment.line"].create(vals_list)
            record.state = "computed"
        return True

    # ------------------------------------------------------------------
    # Critica
    # ------------------------------------------------------------------

    def _check_accounts_configured(self):
        """The closing accounts come from the core tax group."""
        self.ensure_one()
        group = self.tax_group_id.with_company(self.company_id)
        missing = []
        if not group.property_tax_payable_account_id:
            missing.append(_("conta de imposto a pagar"))
        if not group.property_tax_receivable_account_id:
            missing.append(_("conta de imposto a recuperar"))
        if missing:
            raise UserError(
                _(
                    "Configure no grupo de imposto %(group)s, para a empresa "
                    "%(company)s: %(missing)s."
                )
                % {
                    "group": group.display_name,
                    "company": self.company_id.display_name,
                    "missing": ", ".join(missing),
                }
            )
        return group

    def action_post(self):
        """Create the closing journal entry and close the assessment."""
        for record in self:
            if record.state != "computed":
                raise UserError(_("Apure antes de encerrar."))
            group = record._check_accounts_configured()
            if record.company_id.currency_id.is_zero(record.balance):
                # A period with no movement creates no entry but still closes:
                # that is what keeps the credit balance chain without a gap.
                record.state = "posted"
                continue
            record.move_id = record._create_closing_move(group)
            record.state = "posted"
        return True

    def _get_closing_journal(self):
        self.ensure_one()
        journal = self.env["account.journal"].search(
            [("type", "=", "general"), ("company_id", "=", self.company_id.id)],
            limit=1,
        )
        if not journal:
            raise UserError(
                _("Não há diário do tipo Diversos na empresa %s.")
                % self.company_id.display_name
            )
        return journal

    def _prepare_closing_move_lines(self, group):
        """Two entries: move the period balance between the group accounts.

        The entry closes the OFFSETTING (debits against credits). Deductions,
        withholding and special debits are left out on purpose: each has its own
        counterpart account, which the core tax group does not model, and making
        one up here would silently produce a wrong entry.
        """
        self.ensure_one()
        payable = group.property_tax_payable_account_id
        receivable = group.property_tax_receivable_account_id
        balance = self.balance
        label = _("Apuração %s") % self.name

        if balance > 0:
            # tax due: move the net amount to the tax payable account
            return [
                (
                    0,
                    0,
                    {
                        "name": label,
                        "account_id": receivable.id,
                        "debit": 0.0,
                        "credit": balance,
                    },
                ),
                (
                    0,
                    0,
                    {
                        "name": label,
                        "account_id": payable.id,
                        "debit": balance,
                        "credit": 0.0,
                    },
                ),
            ]
        # credit balance: the amount stays as recoverable tax
        return [
            (
                0,
                0,
                {
                    "name": label,
                    "account_id": receivable.id,
                    "debit": -balance,
                    "credit": 0.0,
                },
            ),
            (
                0,
                0,
                {
                    "name": label,
                    "account_id": payable.id,
                    "debit": 0.0,
                    "credit": -balance,
                },
            ),
        ]

    def _create_closing_move(self, group):
        self.ensure_one()
        return self.env["account.move"].create(
            {
                "journal_id": self._get_closing_journal().id,
                "company_id": self.company_id.id,
                "date": self.date_to,
                "ref": _("Encerramento da apuração %s") % self.name,
                "line_ids": self._prepare_closing_move_lines(group),
            }
        )

    def action_draft(self):
        for record in self:
            if record.move_id and record.move_id.state == "posted":
                raise UserError(
                    _(
                        "O lançamento de encerramento %s está postado. Estorne-o "
                        "antes de reabrir a apuração."
                    )
                    % record.move_id.display_name
                )
            record.move_id.unlink()
            record.state = "draft"
        return True

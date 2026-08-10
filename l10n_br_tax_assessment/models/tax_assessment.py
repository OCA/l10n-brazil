# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import _, api, fields, models
from odoo.exceptions import UserError

# Sinal da memoria de calculo. O `account_tax_balance` da OCA ja devolve o
# saldo com o sinal invertido (`-balance`), de modo que imposto de saida
# (credito contabil) sai POSITIVO. Mantemos essa convencao: debito da conta
# grafica = imposto devido pelas saidas; credito = imposto a recuperar das
# entradas.
KIND_DEBIT = "debit"
KIND_CREDIT = "credit"
KIND_DEDUCTION = "deduction"
KIND_WITHHOLDING = "withholding"
KIND_SPECIAL_DEBIT = "special_debit"


class TaxAssessment(models.Model):
    """Apuracao de imposto sobre consumo em um periodo.

    E um LOTE, no mesmo padrao das demais rotinas de periodo da casa: tem
    estado, memoria de calculo persistida, critica e um artefato final (o
    lancamento de encerramento).

    A razao de existir: os blocos E (EFD ICMS/IPI) e M (EFD Contribuicoes) sao
    SAIDAS de uma apuracao, nao calculos proprios. Sem esta camada, cada
    escrituracao recalcula do zero e os numeros nao fecham entre si nem com a
    contabilidade. Com ela, as escrituracoes apenas serializam o que ja foi
    apurado e conferido.

    Os totais publicados aqui seguem, um a um, a estrutura do E110 da EFD
    ICMS/IPI, que e o confronto que a legislacao define. Isso e deliberado: e o
    que permite ao registro apenas ler, sem nenhuma conta propria.
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
        selection=[
            ("not_applicable", "Não se aplica"),
            ("non_cumulative", "Não cumulativo"),
            ("cumulative", "Cumulativo"),
        ],
        default="not_applicable",
        required=True,
        states={"draft": [("readonly", False)]},
        readonly=True,
        help="Regime apurado. PIS e COFINS têm apuração SEPARADA por regime, "
        "e é assim que o M200 da EFD Contribuições pede: um conjunto de "
        "campos para cada. ICMS e IPI usam 'Não se aplica'.\n"
        "O valor é obrigatório de propósito: um regime nulo faria a chave "
        "única do período deixar de valer, porque no Postgres NULL nunca é "
        "igual a NULL.",
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

    # Totais na ordem do E110. Ver `_compute_totals` para a formula.
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
        """Reproduz o confronto do E110, campo a campo.

        O que separa um "ajuste a débito" de um "estorno de crédito" e um do
        outro de um "débito por saída" e apenas a ORIGEM da linha: apurada das
        move lines, ou ajuste manual com o código da tabela 5.1.1. Os dois
        somam do mesmo lado, mas o fisco quer ver os dois separados.
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
            # Um dos dois e sempre zero: ou ha saldo devedor apurado, ou ha
            # saldo credor a transportar para o periodo seguinte.
            record.assessed_balance = balance if balance > 0 else 0.0
            record.amount_carried_forward = -balance if balance < 0 else 0.0
            # A deducao so abate o que ja foi apurado como devido: nunca gera
            # saldo credor nem valor a recolher negativo.
            record.amount_payable = max(
                record.assessed_balance - totals["deduction"] - totals["withholding"],
                0.0,
            )

    @api.model
    def _total_key_for_line(self, line):
        """Em qual total do E110 a linha entra.

        Linha apurada sempre cai no total "puro" (campos 02 e 06). Linha manual
        cai no campo de ajuste correspondente, e o código da tabela 5.1.1
        refina entre ajuste comum e estorno.
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
        """Contexto que o `account_tax_balance` da OCA espera.

        Reusar esse modulo e deliberado: ele ja sabe ler saldo e base por
        imposto num periodo, separando regular de devolucao, direto das move
        lines. A apuracao LE dali, nao recalcula.
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
        """Impostos do grupo apurado, na empresa da apuração."""
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
        """Monta a memória de cálculo do período a partir das move lines."""
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
                # `type_tax_use` decide o lado da conta grafica: imposto de
                # venda gera debito (devido), imposto de compra gera credito
                # (a recuperar). O `account_tax_balance` ja devolve os dois
                # com sinal positivo, por isso a classificacao e nossa.
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
        """As contas do encerramento vêm do grupo de imposto, do core."""
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
        """Gera o lançamento de encerramento e fecha a apuração."""
        for record in self:
            if record.state != "computed":
                raise UserError(_("Apure antes de encerrar."))
            group = record._check_accounts_configured()
            if record.company_id.currency_id.is_zero(record.balance):
                # Periodo sem movimento nao gera lancamento, mas fecha: e o
                # que mantem a cadeia de saldo credor sem buraco.
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
        """Duas partidas: transfere o saldo do período entre as contas do grupo.

        O lançamento fecha o CONFRONTO (débitos contra créditos). Dedução,
        retenção na fonte e débito especial ficam de fora de propósito: a
        contrapartida de cada um é uma conta própria, que o grupo de imposto
        do core não modela, e inventar uma aqui produziria lançamento errado
        em silêncio.
        """
        self.ensure_one()
        payable = group.property_tax_payable_account_id
        receivable = group.property_tax_receivable_account_id
        balance = self.balance
        label = _("Apuração %s") % self.name

        if balance > 0:
            # devedor: transfere o liquido para a conta de imposto a pagar
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
        # credor: o saldo permanece como imposto a recuperar
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

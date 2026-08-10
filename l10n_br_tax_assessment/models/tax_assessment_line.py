# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

# Fourth digit of COD_AJ_APUR (EFD ICMS/IPI table 5.1.1, published per state).
# The code has 8 positions: 1-2 the state, 3 the assessment kind, 4 the
# ADJUSTMENT KIND and 5-8 a sequence. Digit 4 is what decides which E110 field
# the amount lands in, so it is read from the code instead of asking the user
# to classify it a second time.
#
# Digit 3 tells which assessment the adjustment belongs to: "0" the company's
# own tax (E111) and "1" tax substitution (E220). Confirmed against PVA 6.1.1,
# which rejects E111 with "the 3rd character of this code must be Zero", and
# against the official table for SP, where every own-assessment code is
# SP0xnnnn.
APURACAO_PROPRIA, APURACAO_ST = "0", "1"

ADJUSTMENT_KIND_BY_DIGIT = {
    "0": "other_debit",
    "1": "credit_reversal",
    "2": "other_credit",
    "3": "debit_reversal",
    "4": "deduction",
    "5": "special_debit",
}

# Where each adjustment kind lands in the running account. A credit reversal
# adds to the debit side and a debit reversal adds to the credit side, which is
# why neither can be treated as "just another adjustment".
KIND_BY_ADJUSTMENT_KIND = {
    "other_debit": "debit",
    "credit_reversal": "debit",
    "other_credit": "credit",
    "debit_reversal": "credit",
    "deduction": "deduction",
    "special_debit": "special_debit",
}


class TaxAssessmentLine(models.Model):
    """Assessment breakdown, one line per tax or per adjustment.

    This is the table the tax books serialize. EFD ICMS/IPI record E110 and EFD
    Contribuicoes record M200 read from here instead of recomputing, which is
    what keeps the tax book, the accounting and the payment slip on the same
    number.

    Lines with `source=manual` cover the adjustments that do not come from move
    lines. EFD record E111 is exactly that: debit reversals, other credits and
    court-ordered adjustments.
    """

    _name = "l10n_br_tax.assessment.line"
    _description = "Linha da Apuração de Imposto"
    _order = "assessment_id, kind, tax_id"

    assessment_id = fields.Many2one(
        comodel_name="l10n_br_tax.assessment",
        string="Apuração",
        required=True,
        ondelete="cascade",
        index=True,
    )
    company_id = fields.Many2one(
        related="assessment_id.company_id", store=True, readonly=True
    )
    currency_id = fields.Many2one(related="assessment_id.currency_id", readonly=True)
    tax_id = fields.Many2one(
        comodel_name="account.tax",
        string="Imposto",
        ondelete="restrict",
    )
    kind = fields.Selection(
        selection=[
            ("debit", "Débito (saídas)"),
            ("credit", "Crédito (entradas)"),
            ("deduction", "Dedução"),
            ("withholding", "Retenção na fonte"),
            ("special_debit", "Débito especial (extra-apuração)"),
        ],
        required=True,
        help="De que lado da conta gráfica a linha entra. Dedução e retenção "
        "na fonte abatem o saldo devedor já apurado, e débito especial é "
        "extra-apuração: nenhum dos três entra no confronto de débitos com "
        "créditos. Retenção é separada de dedução porque o M200 da EFD "
        "Contribuições pede as duas em campos distintos.",
    )
    source = fields.Selection(
        selection=[
            ("computed", "Apurado das move lines"),
            ("manual", "Ajuste manual"),
        ],
        default="computed",
        required=True,
        help="Ajuste manual sobrevive ao recálculo da apuração; linha apurada "
        "é refeita a cada apuração.",
    )
    description = fields.Char(
        help="Obrigatório no ajuste manual: é o que justifica a linha para o "
        "fisco e alimenta a descrição do registro de ajuste na EFD."
    )
    base_amount = fields.Monetary(string="Base de cálculo")
    tax_amount = fields.Monetary(string="Valor do imposto")

    adjustment_code = fields.Char(
        string="Código do ajuste",
        size=8,
        help="COD_AJ_APUR da tabela 5.1.1, publicada por UF. É o que o E111 "
        "exige e o que classifica o ajuste dentro do E110.",
    )
    adjustment_kind = fields.Selection(
        selection=[
            ("other_debit", "Outros débitos"),
            ("credit_reversal", "Estorno de créditos"),
            ("other_credit", "Outros créditos"),
            ("debit_reversal", "Estorno de débitos"),
            ("deduction", "Deduções"),
            ("special_debit", "Débito especial"),
        ],
        compute="_compute_adjustment_kind",
        store=True,
        help="Lido do quarto dígito do código do ajuste.",
    )

    @api.depends("adjustment_code")
    def _compute_adjustment_kind(self):
        for line in self:
            code = (line.adjustment_code or "").strip()
            line.adjustment_kind = (
                ADJUSTMENT_KIND_BY_DIGIT.get(code[3]) if len(code) >= 4 else False
            )

    @api.constrains("adjustment_code")
    def _check_adjustment_code(self):
        for line in self:
            code = (line.adjustment_code or "").strip()
            if not code:
                continue
            if len(code) != 8 or not code.isalnum():
                raise ValidationError(
                    _(
                        "O código de ajuste %s não tem as 8 posições da tabela "
                        "5.1.1 (UF, tipo de apuração, tipo de ajuste e "
                        "sequencial)."
                    )
                    % code
                )
            if code[2] not in (APURACAO_PROPRIA, APURACAO_ST):
                raise ValidationError(
                    _(
                        "O código de ajuste %s tem um terceiro dígito "
                        "inválido: ele diz de qual apuração é o ajuste, e só "
                        "aceita 0 (imposto próprio) ou 1 (substituição "
                        "tributária)."
                    )
                    % code
                )
            if not line.adjustment_kind:
                raise ValidationError(
                    _(
                        "O código de ajuste %s tem um quarto dígito fora da "
                        "tabela 5.1.1: só 0 a 5 são tipos de ajuste válidos."
                    )
                    % code
                )

    @api.constrains("adjustment_code", "kind")
    def _check_kind_matches_adjustment(self):
        """The adjustment code wins: it is what the tax authority reads.

        Letting the user classify it again would allow a credit reversal to be
        booked as a credit, flipping the sign of the tax due with nothing to
        flag it.
        """
        for line in self:
            if not line.adjustment_kind:
                continue
            expected = KIND_BY_ADJUSTMENT_KIND[line.adjustment_kind]
            if line.kind != expected:
                raise ValidationError(
                    _(
                        "O código de ajuste %(code)s é do tipo %(kind)s, que "
                        "entra na apuração como %(expected)s, e não como "
                        "%(got)s."
                    )
                    % {
                        "code": line.adjustment_code,
                        "kind": line.adjustment_kind,
                        "expected": expected,
                        "got": line.kind,
                    }
                )

    @api.constrains("source", "description")
    def _check_manual_has_description(self):
        for line in self:
            if line.source == "manual" and not (line.description or "").strip():
                raise ValidationError(
                    _(
                        "Ajuste manual sem descrição: é ela que justifica a "
                        "linha para o fisco e alimenta o registro de ajuste "
                        "da EFD."
                    )
                )

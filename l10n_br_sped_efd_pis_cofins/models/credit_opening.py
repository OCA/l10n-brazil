# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class CreditOpening(models.Model):
    """Opening balance of the PIS/COFINS credit of a company that already had
    accumulated credit when it began to use the system.

    The credit of the earlier periods is controlled in the registers 1100 (PIS)
    and 1500 (COFINS) of the EFD Contribuicoes, one for each period of origin and
    type of credit. For a company that comes from another system, the values are
    the ones of those registers in the last EFD Contribuicoes transmitted by the
    previous system. They enter the control as the oldest credit (used first), and
    the assessment of the first period of the system starts from their total.
    """

    _name = "l10n_br_pis_cofins.credit.opening"
    _description = "Saldo inicial de crédito de PIS/COFINS"
    _order = "company_id, tax_domain, origin_period, cod_cred"

    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Empresa",
        required=True,
        default=lambda self: self.env.company,
    )
    currency_id = fields.Many2one(related="company_id.currency_id")
    tax_domain = fields.Selection(
        selection=[("pis", "PIS/PASEP"), ("cofins", "COFINS")],
        string="Tributo",
        required=True,
    )
    cutoff_date = fields.Date(
        string="Primeiro período no sistema",
        required=True,
        help="Primeiro dia do primeiro mês escriturado pelo sistema. O saldo vale "
        "a partir dele: a apuração desse mês parte da soma dos saldos.",
    )
    origin_period = fields.Date(
        string="Período de origem do crédito",
        required=True,
        help="Primeiro dia do mês da apuração em que o crédito nasceu (campo "
        "PER_APU_CRED dos registros 1100 e 1500: mês e ano).",
    )
    cod_cred = fields.Char(
        string="Tipo de crédito",
        required=True,
        default="101",
        size=3,
        help="Código do tipo de crédito, tabela 4.3.6 da EFD Contribuições "
        "(101: crédito vinculado à receita tributada no mercado interno, alíquota "
        "básica).",
    )
    orig_cred = fields.Selection(
        selection=[
            ("01", "Operações próprias"),
            ("02", "Transferido por pessoa jurídica sucedida"),
        ],
        string="Origem do crédito",
        required=True,
        default="01",
    )
    cnpj_suc = fields.Char(
        string="CNPJ da cedente",
        help="CNPJ da pessoa jurídica que cedeu o crédito, só quando a origem é "
        "'Transferido por pessoa jurídica sucedida'.",
    )
    amount = fields.Monetary(
        string="Crédito apurado",
        required=True,
        help="Valor total do crédito apurado no período de origem (campo "
        "VL_TOT_CRED_APU dos registros 1100 e 1500 da última EFD Contribuições "
        "transmitida pelo sistema anterior).",
    )
    used_before = fields.Monetary(
        string="Já utilizado antes do sistema",
        help="Valor desse crédito já usado nos períodos anteriores ao primeiro do "
        "sistema (desconto, ressarcimento, compensação e outros).",
    )
    balance = fields.Monetary(
        string="Saldo", compute="_compute_balance", store=True, readonly=True
    )

    @api.depends("amount", "used_before")
    def _compute_balance(self):
        for record in self:
            record.balance = round(record.amount - record.used_before, 2)

    @api.constrains("amount", "used_before")
    def _check_amounts(self):
        for record in self:
            if record.amount < 0 or record.used_before < 0:
                raise ValidationError(_("The credit values cannot be negative."))
            if record.used_before > record.amount:
                raise ValidationError(
                    _("The credit already used cannot be above the credit assessed.")
                )

    @api.constrains("origin_period", "cutoff_date")
    def _check_periods(self):
        for record in self:
            if record.origin_period.day != 1 or record.cutoff_date.day != 1:
                raise ValidationError(
                    _("Inform the first day of the month in the periods.")
                )
            if record.origin_period >= record.cutoff_date:
                raise ValidationError(
                    _(
                        "The period of origin of the credit has to be before the "
                        "first period of the system."
                    )
                )

    @api.constrains("orig_cred", "cnpj_suc")
    def _check_assignor(self):
        for record in self:
            if record.orig_cred == "02" and not record.cnpj_suc:
                raise ValidationError(
                    _(
                        "Inform the CNPJ of the assignor of a credit that was "
                        "transferred."
                    )
                )

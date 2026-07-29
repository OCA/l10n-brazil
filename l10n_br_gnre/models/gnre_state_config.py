# Copyright 2026 KMEE - Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

GNRE_MODE = [
    ("document", "Uma guia por documento"),
    ("consolidated", "Guia consolidada no período"),
]

# Qual valor da linha fiscal alimenta a obrigação. Não dá para derivar isso do
# grupo de imposto: o DIFAL não tem grupo nem tax_domain proprios, o valor vive
# como icms_destination_value dentro do domínio icms.
GNRE_AMOUNT_SOURCE = [
    ("icmsst", "ICMS ST e FCP ST"),
    ("difal", "DIFAL e FCP destino"),
]

GNRE_PERIOD = [
    ("0", "Mensal"),
    ("1", "1a. quinzena"),
    ("2", "2a. quinzena"),
    ("3", "1o. decêndio"),
    ("4", "2o. decêndio"),
    ("5", "3o. decêndio"),
]


class GnreStateConfig(models.Model):
    """Regras de recolhimento da GNRE por UF favorecida.

    A escolha entre guia por documento e guia consolidada não é do imposto: ela
    depende da UF e de a empresa ter ou não inscrição estadual naquele destino.
    Sem inscrição, o recolhimento é por operação e a guia paga acompanha a
    mercadoria; com inscrição, apura-se o período e recolhe-se de uma vez.
    """

    _name = "l10n_br_gnre.state.config"
    _description = "GNRE State Configuration"
    _rec_name = "fiscal_state_id"
    _order = "company_id, fiscal_state_id"

    company_id = fields.Many2one(
        comodel_name="res.company",
        required=True,
        default=lambda self: self.env.company,
    )

    fiscal_state_id = fields.Many2one(
        comodel_name="res.country.state",
        string="UF Favorecida",
        required=True,
        domain=lambda self: [("country_id", "=", self.env.ref("base.br").id)],
    )

    tax_group_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.tax.group",
        string="Grupo Fiscal",
        required=True,
        domain=[("tax_scope", "=", "state")],
        help="Grupo de imposto que esta regra atende, por exemplo ICMS ST.",
    )

    amount_source = fields.Selection(
        selection=GNRE_AMOUNT_SOURCE,
        string="Origem do Valor",
        required=True,
        default="icmsst",
        help="Quais valores da linha fiscal alimentam a obrigação.",
    )

    authority_partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Secretaria da Fazenda",
        help="Credor da guia. Quando vazio, o módulo de integração contábil "
        "resolve pelo parceiro marcado como SEFAZ daquele estado.",
    )

    revenue_code = fields.Char(
        string="Código de Receita",
        required=True,
        help="Código de receita da tabela do convênio, próprio de cada UF.",
    )

    detail_revenue_code = fields.Char(
        string="Detalhamento da Receita",
    )

    mode = fields.Selection(
        selection=GNRE_MODE,
        string="Modo",
        required=True,
        default="document",
        help="Por documento: uma guia por nota, que acompanha a mercadoria. "
        "Consolidada: uma guia por período para todas as notas da mesma UF e "
        "código de receita.",
    )

    period = fields.Selection(
        selection=GNRE_PERIOD,
        string="Período de Apuração",
        default="0",
    )

    due_days = fields.Integer(
        string="Prazo em Dias",
        default=0,
        help="Dias entre a data do documento e o vencimento da guia. Zero "
        "significa vencimento na data do documento, o caso de quem não tem "
        "inscrição estadual no destino e recolhe antes da saída.",
    )

    convenio = fields.Char(
        string="Convênio",
    )

    active = fields.Boolean(default=True)

    _sql_constraints = [
        (
            "state_source_uniq",
            "unique (company_id, fiscal_state_id, amount_source)",
            "Já existe uma regra de GNRE para esta UF e origem de valor.",
        )
    ]

    @api.constrains("mode", "period")
    def _check_period(self):
        for record in self:
            if record.mode == "consolidated" and not record.period:
                raise ValidationError(
                    _("Guia consolidada exige um período de apuração.")
                )

    @api.model
    def _find_config(self, company, fiscal_state, amount_source):
        """Return the config that applies, or an empty recordset."""
        return self.search(
            [
                ("company_id", "=", company.id),
                ("fiscal_state_id", "=", fiscal_state.id),
                ("amount_source", "=", amount_source),
            ],
            limit=1,
        )

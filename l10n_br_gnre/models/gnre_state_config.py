# Copyright 2026 KMEE - Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

from .document import _value

# Consulta de configurações da UF (manual, item 4.3): 450 é a consulta efetuada.
CONFIG_OK = "450"

# Campos extras cujo valor sai do documento de origem, pelo título que a UF
# publica na consulta de configurações. Os demais ficam como texto fixo.
EXTRA_SOURCE_BY_TITLE = {
    "data de emissão": "document_date",
    "chave de acesso": "document_key",
    "chave da nfe": "document_key",
    "número do documento": "document_number",
}

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

    recipient_required = fields.Boolean(
        string="Informar Destinatário",
        help="A UF exige o contribuinte destinatário no item da guia, o que é "
        "comum no DIFAL de venda a consumidor final. Confira na consulta de "
        "configurações da UF (GnreConfigUF) para a receita.",
    )

    origin_document_type = fields.Char(
        string="Tipo do Documento de Origem",
        default="10",
        help="Código do tipo de documento de origem que a UF aceita para a "
        "receita, informado na consulta de configurações da UF (por exemplo "
        "10, nota fiscal, ou 24, chave do DF-e).",
    )

    period_reference = fields.Boolean(
        string="Informar Período de Referência",
        default=True,
        help="Envia a referência (período, mês e ano) no item da guia.",
    )

    payment_date_required = fields.Boolean(
        string="Informar Data de Pagamento",
        help="A UF exige a data de pagamento na guia; vai a data de vencimento.",
    )

    fcp_required = fields.Boolean(
        string="FCP Sempre Informado",
        help="A UF exige o valor do FCP no item, mesmo quando é zero.",
    )

    extra_field_ids = fields.One2many(
        comodel_name="l10n_br_gnre.state.config.extra",
        inverse_name="config_id",
        string="Campos Extras",
        help="Campos adicionais que a UF exige no item, no máximo três.",
    )

    portal_rules = fields.Text(
        string="Regras do Portal",
        readonly=True,
        help="Resumo da última consulta de configurações da UF no portal.",
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

    @api.constrains("extra_field_ids")
    def _check_extra_fields(self):
        for record in self:
            if len(record.extra_field_ids) > 3:
                raise ValidationError(
                    _("O item da guia aceita no máximo três campos extras.")
                )

    def action_gnre_fetch_rules(self):
        """Fill the rule with what the portal requires for the revenue.

        Reads the GnreConfigUF answer of the favoured state for the revenue
        code and sets the recipient, the origin document type, the payment
        date, the FCP and the mandatory extra fields accordingly.
        """
        self.ensure_one()
        client = self.company_id._gnre_client()
        answer = client.consulta_config_uf(
            uf=self.fiscal_state_id.code, receita=self.revenue_code
        )
        situation = answer.situacaoConsulta
        code = _value(situation.codigo) if situation else False
        if code != CONFIG_OK:
            message = _value(situation.descricao) if situation else ""
            raise UserError(
                _(
                    "O portal recusou a consulta: %(code)s %(message)s",
                    code=code or "",
                    message=message,
                )
            )
        revenue = next(
            (
                item
                for item in (answer.receitas.receita if answer.receitas else [])
                if _value(item.codigo) == self.revenue_code
            ),
            None,
        )
        if revenue is None:
            raise UserError(
                _(
                    "A UF %(state)s não gera GNRE para a receita %(revenue)s.",
                    state=self.fiscal_state_id.code,
                    revenue=self.revenue_code,
                )
            )
        self.write(self._gnre_rules_values(revenue))
        return True

    def _gnre_rules_values(self, revenue):
        def required(node):
            return _value(node) == "S"

        values = {
            "recipient_required": required(revenue.exigeContribuinteDestinatario),
            "period_reference": required(revenue.exigePeriodoReferencia),
            "payment_date_required": required(revenue.exigeDataPagamento),
            "fcp_required": required(revenue.exigeValorFecp),
        }
        origin_types = (
            revenue.tiposDocumentosOrigem.tipoDocumentoOrigem
            if revenue.tiposDocumentosOrigem
            else []
        )
        if origin_types:
            values["origin_document_type"] = _value(origin_types[0].codigo)
        extras = [(5, 0, 0)]
        summary = []
        additional = (
            revenue.camposAdicionais.campoAdicional if revenue.camposAdicionais else []
        )
        for extra in additional:
            title = _value(extra.titulo) or ""
            mandatory = required(extra.obrigatorio)
            summary.append(
                f"{_value(extra.codigo)} {title}"
                + (" (obrigatório)" if mandatory else "")
            )
            if mandatory:
                extras.append(
                    (
                        0,
                        0,
                        {
                            "code": int(_value(extra.codigo)),
                            "name": title,
                            "field_type": _value(extra.tipo),
                            "source": EXTRA_SOURCE_BY_TITLE.get(title.lower(), "fixed"),
                        },
                    )
                )
        values["extra_field_ids"] = extras
        values["portal_rules"] = "\n".join(
            [
                _("Destinatário: %s") % _value(revenue.exigeContribuinteDestinatario),
                _("Documento de origem: %s")
                % ", ".join(
                    f"{_value(t.codigo)} {_value(t.descricao)}" for t in origin_types
                ),
                _("Data de pagamento: %s") % _value(revenue.exigeDataPagamento),
                _("FCP: %s") % _value(revenue.exigeValorFecp),
                _("Detalhamento: %s") % _value(revenue.exigeDetalhamentoReceita),
                _("Produto: %s") % _value(revenue.exigeProduto),
                _("Campos extras: %s") % ("; ".join(summary) or "-"),
            ]
        )
        return values

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

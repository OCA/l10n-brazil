# Copyright 2026 KMEE - Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError

# Um item de guia comporta no máximo 100 ocorrências no layout 2.00.
GNRE_MAX_ITEMS = 100

OBLIGATION_STATE = [
    ("pending", "Pendente"),
    ("grouped", "Agrupada"),
    ("transmitted", "Transmitida"),
    ("paid", "Paga"),
    ("cancelled", "Cancelada"),
]


class GnreObligation(models.Model):
    """Obrigação de recolhimento que dá origem a um item de guia GNRE.

    Nasce do fato gerador (a nota com ICMS-ST, FCP ou DIFAL) e vive até virar
    item de uma guia. A granularidade acompanha o que o XSD 2.00 representa:
    um `itensGNRE/item` é a chave (documento de origem, receita, detalhamento
    da receita, período, vencimento). ICMS principal e FCP são dois `valor` do
    mesmo item, e não obrigações separadas.

    Os nomes de campo seguem os registros E116 e E250 do EFD ICMS/IPI, onde o
    SPED representa a mesma coisa. Isso é de graça e torna o mapeamento futuro
    quase literal.

    Note que a obrigação materializa a UF favorecida em vez de derivá-la do
    parceiro: o endereço do parceiro muda depois, a UF da obrigação já criada
    não pode mudar.
    """

    _name = "l10n_br_gnre.obligation"
    _description = "GNRE Tax Obligation"
    _order = "date_due, fiscal_state_id, id"

    name = fields.Char(
        compute="_compute_name",
        store=True,
    )

    company_id = fields.Many2one(
        comodel_name="res.company",
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )

    document_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.document",
        string="Documento de Origem",
        ondelete="cascade",
        index=True,
    )

    config_id = fields.Many2one(
        comodel_name="l10n_br_gnre.state.config",
        string="Regra da UF",
        required=True,
    )

    fiscal_state_id = fields.Many2one(
        comodel_name="res.country.state",
        string="UF Favorecida",
        required=True,
        index=True,
        help="Materializada no momento do fato gerador, ver E200.UF.",
    )

    tax_group_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.tax.group",
        string="Grupo Fiscal",
        required=True,
    )

    authority_partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Secretaria da Fazenda",
    )

    obligation_code = fields.Char(
        string="Código da Obrigação",
        help="COD_OR do EFD, tabela 5.4.",
    )

    revenue_code = fields.Char(
        string="Código de Receita",
        required=True,
        help="COD_REC do EFD. Char e não Selection: a tabela varia por UF.",
    )

    detail_revenue_code = fields.Char(
        string="Detalhamento da Receita",
    )

    amount_principal = fields.Monetary(
        string="Principal",
        currency_field="currency_id",
    )

    amount_fcp = fields.Monetary(
        string="FCP",
        currency_field="currency_id",
        help="Vai no mesmo item da guia, como valor de código 12.",
    )

    amount_fine = fields.Monetary(
        string="Multa",
        currency_field="currency_id",
    )

    amount_interest = fields.Monetary(
        string="Juros",
        currency_field="currency_id",
    )

    amount_total = fields.Monetary(
        string="Total",
        compute="_compute_amount_total",
        store=True,
        currency_field="currency_id",
        help="VL_OR do EFD.",
    )

    currency_id = fields.Many2one(
        comodel_name="res.currency",
        default=lambda self: self.env.ref("base.BRL"),
        required=True,
    )

    period_ref = fields.Char(
        string="Competência",
        size=6,
        help="MES_REF do EFD, no formato mmaaaa.",
    )

    date_start = fields.Date(string="Início do Período")
    date_end = fields.Date(string="Fim do Período")

    date_due = fields.Date(
        string="Vencimento",
        required=True,
        index=True,
        help="DT_VCTO do EFD.",
    )

    guide_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.document",
        string="Guia",
        readonly=True,
        copy=False,
        index=True,
        help="Guia que consumiu esta obrigação. Vazio enquanto pendente.",
    )

    state = fields.Selection(
        selection=OBLIGATION_STATE,
        default="pending",
        required=True,
        readonly=True,
        copy=False,
        index=True,
    )

    @api.depends("fiscal_state_id", "revenue_code", "document_id")
    def _compute_name(self):
        for record in self:
            parts = [
                record.fiscal_state_id.code or "",
                record.revenue_code or "",
            ]
            if record.document_id:
                parts.append(record.document_id.document_number or "")
            record.name = "/".join(p for p in parts if p)

    @api.depends("amount_principal", "amount_fcp", "amount_fine", "amount_interest")
    def _compute_amount_total(self):
        for record in self:
            record.amount_total = (
                record.amount_principal
                + record.amount_fcp
                + record.amount_fine
                + record.amount_interest
            )

    @api.model
    def _prepare_from_document(self, document, config, values):
        """Build the values of one obligation out of a fiscal document.

        `values` carries the amounts already computed by the caller, which is
        the module that knows where they come from: the accounting glue reads
        the fiscal lines, an import may read the XML.
        """
        document_date = fields.Date.to_date(document.document_date)
        date_due = document_date + relativedelta(days=config.due_days)
        result = {
            "company_id": document.company_id.id,
            "document_id": document.id,
            "config_id": config.id,
            "fiscal_state_id": config.fiscal_state_id.id,
            "tax_group_id": config.tax_group_id.id,
            "authority_partner_id": config.authority_partner_id.id,
            "revenue_code": config.revenue_code,
            "detail_revenue_code": config.detail_revenue_code,
            "date_due": date_due,
            "period_ref": document_date.strftime("%m%Y"),
        }
        result.update(values)
        return result

    def _group_key(self):
        """Key that decides which obligations share the same guide.

        In consolidated mode the document is out of the key, so every note of
        the period lands on the same guide. Per document mode puts it back in,
        and the grouping falls to one guide per note by construction.
        """
        self.ensure_one()
        key = (
            self.company_id.id,
            self.fiscal_state_id.id,
            self.revenue_code,
            self.detail_revenue_code or "",
            self.period_ref or "",
            self.date_due,
        )
        if self.config_id.mode == "document":
            key = key + (self.document_id.id,)
        return key

    def _check_groupable(self):
        for record in self:
            if record.state != "pending":
                raise UserError(
                    _(
                        "A obrigação %(name)s não está pendente e não pode "
                        "entrar numa guia.",
                        name=record.display_name,
                    )
                )

    def group_for_guides(self):
        """Split the recordset into batches, one per guide to be issued.

        Respects the hard limit of 100 items per guide from the layout: a
        group larger than that becomes more than one guide, and no obligation
        is left out.
        """
        self._check_groupable()
        groups = {}
        for record in self:
            groups.setdefault(record._group_key(), self.browse())
            groups[record._group_key()] |= record

        batches = []
        for obligations in groups.values():
            ordered = obligations.sorted(lambda o: o.id)
            for start in range(0, len(ordered), GNRE_MAX_ITEMS):
                batches.append(ordered[start : start + GNRE_MAX_ITEMS])
        return batches

    def action_cancel(self):
        for record in self:
            if record.state in ("transmitted", "paid"):
                raise UserError(
                    _(
                        "A obrigação %(name)s já foi transmitida e não pode "
                        "ser cancelada por aqui.",
                        name=record.display_name,
                    )
                )
        self.write({"state": "cancelled"})

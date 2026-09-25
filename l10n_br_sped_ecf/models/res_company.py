# Copyright (C) 2026 Luis Felipe Mileo - KMEE <mileo@kmee.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    l10n_br_ecf_shareholder_ids = fields.One2many(
        comodel_name="l10n_br_ecf.shareholder",
        inverse_name="company_id",
        string="Socios na ECF",
        help="Socios e titulares informados no registro Y600.",
    )

    l10n_br_ecf_profit_period = fields.Selection(
        selection=[
            ("T", "T - Trimestral"),
            ("A", "A - Anual (estimativa mensal)"),
        ],
        string="Apuracao do IRPJ e da CSLL",
        default="T",
        help="Periodo de apuracao do IRPJ e da CSLL declarado no registro "
        "0010 (campo FORMA_APUR) e usado nos registros de periodo (K030, "
        "P030, L030, M030, N030). O lucro presumido apura sempre por "
        "trimestre, por forca de lei, e ignora esta escolha; o lucro real "
        "pode apurar por trimestre ou no ano, por estimativa mensal.",
    )

    l10n_br_ecf_monthly_estimate = fields.Selection(
        selection=[
            ("E", "E - Receita bruta e acrescimos"),
            ("B", "B - Balanco ou balancete de suspensao ou reducao"),
        ],
        string="Estimativa mensal na ECF",
        default="E",
        help="Como a empresa determinou a estimativa mensal do IRPJ e da "
        "CSLL, informado no registro 0010 (campo MES_BAL_RED). So se aplica "
        "ao lucro real com apuracao anual.",
    )

    l10n_br_ecf_stock_valuation = fields.Selection(
        # dominio oficial do campo IND_AVAL_ESTOQ do Y672 (tabela do leiaute);
        # valores fora dela sao reprovados pelo validador da Receita
        selection=[
            ("1", "1 - Custo medio ponderado"),
            ("2", "2 - PEPS"),
            ("3", "3 - Arbitramento"),
            ("4", "4 - Custo especifico"),
            ("5", "5 - Valor realizavel liquido"),
            ("6", "6 - Inventario periodico"),
            ("7", "7 - Outros"),
            ("8", "8 - Nao ha (prestadoras de servicos)"),
        ],
        string="Avaliacao do estoque na ECF",
        default="1",
        help="Criterio de avaliacao do estoque final informado no registro "
        "Y672 (campo IND_AVAL_ESTOQ).",
    )

    l10n_br_ecf_revenue_recognition = fields.Selection(
        selection=[
            ("accrual", "Competencia"),
            ("cash", "Caixa"),
        ],
        string="Reconhecimento da receita (presumido)",
        default="accrual",
        help="Criterio de reconhecimento das receitas do lucro presumido "
        "(0010.IND_REC_RECEITA, art. 215, par. 9, da IN RFB 1700/2017). A "
        "opcao pelo caixa e exercida no recolhimento do primeiro DARF do ano "
        "e vale para IRPJ, CSLL, PIS e COFINS ao mesmo tempo. Este modulo "
        "apura por competencia: a empresa optante pelo caixa nao deve gerar "
        "a ECF por aqui ate que a apuracao pelo recebimento seja suportada.",
    )

# Copyright 2023 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields

from odoo.addons.spec_driven_model.models import spec_models


class Ferroviario(spec_models.SpecModel):
    _name = "l10n_br_cte.ferroviario"
    _inherit = "cte.40.ferrov"

    document_id = fields.One2many(
        comodel_name="l10n_br_fiscal.document", inverse_name="cte40_ferroviario"
    )

    cte40_tpTraf = fields.Selection(
        selection=[
            ("0", "Próprio"),
            ("1", "Mútuo"),
            ("2", "Rodoferroviário"),
            ("3", "Rodoviário."),
        ],
        default="0",
    )

    cte40_fluxo = fields.Char(
        string="Fluxo Ferroviário",
        help=(
            "Fluxo Ferroviário\nTrata-se de um número identificador do "
            "contrato firmado com o cliente"
        ),
    )

    # TRAFMUT
    cte40_trafMut = fields.Many2one(
        comodel_name="l10n_br_fiscal.document",
        string="Detalhamento de informações",
        help="Detalhamento de informações para o tráfego mútuo",
    )

    cte40_vFrete = fields.Monetary(
        related="cte40_trafMut.amount_freight_value",
        currency_field="brl_currency_id",
    )

    cte40_respFat = fields.Selection(
        selection=[
            ("1", "Ferrovia de origem"),
            ("2", "Ferrovia de destino"),
        ]
    )

    cte40_ferrEmi = fields.Selection(
        selection=[
            ("1", "Ferrovia de origem"),
            ("2", "Ferrovia de destino"),
        ],
        string="Ferrovia Emitente do CTe",
        help=(
            "Ferrovia Emitente do CTe\nPreencher com: "
            "\n\t\t\t\t\t\t\t\t\t1-Ferrovia de origem; "
            "\n\t\t\t\t\t\t\t\t\t2-Ferrovia de destino"
        ),
    )

    cte40_ferroEnv = fields.One2many(
        comodel_name="l10n_br_cte.ferroenv",
        inverse_name="cte40_cInt",
        string="Informações das Ferrovias Envolvidas",
    )

    def export_data(self):
        return {
            "cte40_tpTraf": self.cte40_tpTraf,
            "cte40_fluxo": self.cte40_fluxo,
            "cte40_vFrete": self.cte40_vFrete,
            "cte40_respFat": self.cte40_respFat,
            "cte40_ferrEmi": self.cte40_ferrEmi,
            "cte40_ferroEnv": self.cte40_ferroEnv,
        }


class FerroEnv(spec_models.SpecModel):
    _name = "l10n_br_cte.ferroenv"
    _inherit = "cte.40.ferroenv"

    partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Ferrovias Envolvidas",
    )

    cte40_cInt = fields.Char(
        related="cInt",
        string="Código interno da Ferrovia envolvida",
        help="Código interno da Ferrovia envolvida\nUso da transportadora",
    )

    cInt = fields.Char()

    def export_data(self):
        return {
            "cte40_cInt": self.cte40_cInt,
            "cte40_CNPJ": self.partner_id.cte40_CNPJ,
            "cte40_IE": self.partner_id.cte40_IE,
            "cte40_xNome": self.partner_id.cte40_xNome,
            "cte40_nro": self.partner_id.cte40_nro,
            "cte40_xLgr": self.partner_id.cte40_xLgr,
            "cte40_xCPL": self.partner_id.cte40_xCPL,
            "cte40_xBairro": self.partner_id.cte40_xBairro,
            "cte40_cMun": self.partner_id.cte40_cMun,
            "cte40_xMun": self.partner_id.cte40_xMun,
            "cte40_CEP": self.partner_id.cte40_CEP,
            "cte40_UF": self.partner_id.cte40_UF,
        }

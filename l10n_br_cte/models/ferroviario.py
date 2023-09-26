# Copyright 2023 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from nfelib.cte.bindings.v4_0.cte_modal_ferroviario_v4_00 import Ferrov, TenderFer

from odoo import api, fields

from odoo.addons.spec_driven_model.models import spec_models


class Ferroviario(spec_models.SpecModel):
    _name = "l10n_br_cte.modal.ferroviario"
    _inherit = "cte.40.ferrov"

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

    cte40_trafMut = fields.Many2one(
        comodel_name="cte.40.modal.trafmut",
        string="Detalhamento de informações",
        help="Detalhamento de informações para o tráfego mútuo",
    )


class TrafMut(spec_models.SpecModel):
    _name = "l10n_br_cte.modal.ferroviario.trafmut"
    _inherit = "cte.40.trafmut"

    cte40_vFrete = fields.Monetary(
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
        comodel_name="l10n_br_cte.modal.ferroviario.trafmut.ferroenv",
        string="Informações das Ferrovias Envolvidas",
    )


class FerroEnv(spec_models.SpecModel):
    _name = "l10n_br_cte.modal.ferroviario.trafmut.ferroenv"
    _inherit = "cte.40.ferroenv"

    document_id = fields.Many2one(comodel_name="l10n_br_fiscal.document")

    partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Ferrovias Envolvidas",
    )

    cte40_cInt = fields.Char(
        string="Código interno da Ferrovia envolvida",
        help="Código interno da Ferrovia envolvida\nUso da transportadora",
    )

    cte40_enderFerro = fields.Many2one(
        comodel_name="cte.40.modal.tenderfer",
        string="Detalhamento de informações",
        help="Detalhamento de informações para o tráfego mútuo",
    )

    @api.model
    def export_fields(self):
        if len(self) > 1:
            return self.export_fields_multi()

        return Ferrov.TrafMut.FerroEnv(
            CNPJ=self.partner_id.cte40_CNPJ,
            IE=self.partner_id.cte40_IE,
            xNome=self.partner_id.cte40_xNome,
            cInt=self.cte40_cInt,
        )

    @api.model
    def export_fields_multi(self):
        return [record.export_fields() for record in self]


class TenderFerrov(spec_models.SpecModel):
    _name = "l10n_br_cte.modal.tenderfer"
    _inherit = "cte.40.tenderfer"

    cte40_xLgr = fields.Char(string="Logradouro")

    cte40_nro = fields.Char(string="Número")

    cte40_xCpl = fields.Char(string="Complemento")

    cte40_xBairro = fields.Char(string="Bairro")

    cte40_cMun = fields.Char(
        string="Código do município",
        help=(
            "Código do município\nUtilizar a tabela do "
            "IBGE\n\t\t\t\t\tInformar 9999999 para operações com o exterior."
        ),
    )

    cte40_xMun = fields.Char(
        string="Nome do município",
        help=("Nome do município\nInformar EXTERIOR para operações com o " "exterior."),
    )

    cte40_CEP = fields.Char(string="CEP")

    cte40_UF = fields.Char(
        string="Sigla da UF",
        help="Sigla da UF\nInformar EX para operações com o exterior.",
    )

    @api.model
    def export_fields(self):
        if len(self) > 1:
            return self.export_fields_multi()

        return TenderFer(
            xLgr=self.cte40_xLgr,
            xBairro=self.cte40_xBairro,
            xMun=self.cte40_xMun,
            cMun=self.cte40_cMun,
            CEP=self.cte40_CEP,
            UF=self.cte40_UF,
            nro=self.cte40_nro,
            xCpl=self.cte40_xCpl,
        )

    @api.model
    def export_fields_multi(self):
        return [record.export_fields() for record in self]

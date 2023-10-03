# Copyright 2023 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from odoo import fields

from odoo.addons.spec_driven_model.models import spec_models


class Ferroviario(spec_models.StackedModel):
    _name = "l10n_br_cte.modal.ferroviario"
    _inherit = "cte.40.ferrov"
    _stacked = "cte.40.ferrov"
    _binding_module = "nfelib.cte.bindings.v4_0.cte_modal_ferroviario_v4_00"
    _field_prefix = "cte40_"
    _schema_name = "cte"
    _schema_version = "4.0.0"
    _odoo_module = "l10n_br_cte"
    _spec_module = (
        "odoo.addons.l10n_br_cte_spec.models.v4_0.cte_modal_ferroviario_v4_00"
    )
    _spec_tab_name = "CTe"
    _description = "Modal Ferroviario CTe"

    document_id = fields.Many2one(comodel_name="l10n_br_fiscal.document")

    cte40_tpTraf = fields.Selection(related="document_id.railroad_traffic_type")

    cte40_fluxo = fields.Char(related="document_id.railroad_flow")

    def _prepare_dacte_values(self):
        if not self:
            return {}


class TrafMut(spec_models.SpecModel):
    _name = "l10n_br_cte.modal.ferroviario.trafmut"
    _inherit = "cte.40.trafmut"
    _binding_module = "nfelib.cte.bindings.v4_0.cte_modal_ferroviario_v4_00"
    _description = "Detalhamento de informações para o tráfego mútuo"

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
    _binding_module = "nfelib.cte.bindings.v4_0.cte_modal_ferroviario_v4_00"
    _description = "Informações das Ferrovias Envolvidas"

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


class TenderFerrov(spec_models.SpecModel):
    _name = "l10n_br_cte.modal.ferroviario.tenderfer"
    _inherit = "cte.40.tenderfer"
    _binding_module = "nfelib.cte.bindings.v4_0.cte_modal_ferroviario_v4_00"
    _description = "Tipo Dados do Endereço"

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

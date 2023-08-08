# Copyright 2023 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields

from odoo.addons.spec_driven_model.models import spec_models


class Aquaviario(spec_models.SpecModel):
    _name = "l10n_br_cte.aquaviario"
    _inherit = "cte.40.aquav"

    document_id = fields.One2many(
        comodel_name="l10n_br_fiscal.document", inverse_name="cte40_aquav"
    )

    cte40_vPrest = fields.Monetary(compute="_compute_vPrest", store=True)

    cte40_vAFRMM = fields.Monetary(
        string="AFRMM",
        currency_field="brl_currency_id",
        help=("AFRMM (Adicional de Frete para Renovação da Marinha Mercante)"),
        store=True,
    )

    cte40_xNavio = fields.Char(string="Identificação do Navio", store=True)

    cte40_nViag = fields.Char(string="Número da Viagem", store=True)

    cte40_direc = fields.Selection(
        selection=[
            ("N", "Norte, L-Leste, S-Sul, O-Oeste"),
            ("S", "Sul, O-Oeste"),
            ("L", "Leste, S-Sul, O-Oeste"),
            ("O", "Oeste"),
        ],
        string="Direção",
        store=True,
        help="Direção\nPreencher com: N-Norte, L-Leste, S-Sul, O-Oeste",
    )

    cte40_irin = fields.Char(
        string="Irin do navio sempre deverá",
        help="Irin do navio sempre deverá ser informado",
        store=True,
    )

    cte40_tpNav = fields.Selection(
        selection=[
            ("0", "Interior"),
            ("1", "Cabotagem"),
        ],
        string="Tipo de Navegação",
        help=(
            "Tipo de Navegação\nPreencher com: \n\t\t\t\t\t\t0 - "
            "Interior;\n\t\t\t\t\t\t1 - Cabotagem"
        ),
        store=True,
    )

    def _compute_vPrest(self):
        for record in self.document_id.fiscal_line_ids:
            record.cte40_vPrest += record.cte40_vTPrest

    def export_data(self):
        return {
            "cte40_vPrest": self.cte40_vPrest,
            "cte40_vAFRMM": self.cte40_vAFRMM,
            "cte40_xNavio": self.cte40_xNavio,
            "cte40_nViag": self.cte40_nViag,
            "cte40_direc": self.cte40_direc,
            "cte40_irin": self.cte40_irin,
            "cte40_tpNav": self.cte40_tpNav,
        }

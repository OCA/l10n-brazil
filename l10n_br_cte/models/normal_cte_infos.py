# Copyright 2023 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields

from odoo.addons.spec_driven_model.models import spec_models


class CTeNormalInfos(spec_models.StackedModel):
    _name = "l10n_br_cte.normal.infos"
    _inherit = ["cte.40.tcte_infctenorm"]
    _stacked = "cte.40.tcte_infctenorm"
    _field_prefix = "cte40_"
    _schema_name = "cte"
    _schema_version = "4.0.0"
    _odoo_module = "l10n_br_cte"
    _spec_module = "odoo.addons.l10n_br_cte_spec.models.v4_0.cte_tipos_basico_v4_00"
    _binding_module = "nfelib.cte.bindings.v4_0.cte_tipos_basico_v4_00"
    _spec_tab_name = "CTe"
    _description = "Grupo de informações do CTe Normal e Substituto"
    _force_stack_paths = "infctenorm.infdoc"

    document_id = fields.Many2one(comodel_name="l10n_br_fiscal.document")

    currency_id = fields.Many2one(
        comodel_name="res.currency",
        related="document_id.company_id.currency_id",
    )

    cte40_vCarga = fields.Monetary(
        related="document_id.cte40_vCarga",
        currency_field="currency_id",
    )

    cte40_proPred = fields.Char(
        related="document_id.cte40_proPred",
    )

    cte40_xOutCat = fields.Char(
        related="document_id.cte40_xOutCat",
    )

    cte40_infQ = fields.One2many(
        comodel_name="l10n_br_cte.cargo.quantity.infos",
        related="document_id.cte40_infQ",
    )

    cte40_vCargaAverb = fields.Monetary(
        related="document_id.cte40_vCargaAverb",
    )

    cte40_veicNovos = fields.One2many(
        comodel_name="l10n_br_cte.transported.vehicles",
        related="document_id.cte40_veicNovos",
    )

    cte40_infNFe = fields.One2many(
        comodel_name="l10n_br_fiscal.document.related",
        related="document_id.document_related_ids",
    )

    cte40_versaoModal = fields.Char(related="document_id.cte40_versaoModal")

    # Campos do Modal Aereo
    modal_aereo_id = fields.Many2one(
        comodel_name="l10n_br_cte.modal.aereo", related="document_id.modal_aereo_id"
    )

    cte40_nMinu = fields.Char(related="document_id.cte40_nMinu")

    cte40_nOCA = fields.Char(related="document_id.cte40_nOCA")

    cte40_dPrevAereo = fields.Date(related="document_id.cte40_dPrevAereo")

    cte40_xDime = fields.Char(related="document_id.cte40_xDime")

    cte40_CL = fields.Char(related="document_id.cte40_CL")

    cte40_cTar = fields.Char(related="document_id.cte40_cTar")

    # Existem dois vTar no spec, um float e um monetary, por isso a mudança de nome
    cte40_aereo_vTar = fields.Monetary(related="document_id.cte40_aereo_vTar")

    cte40_peri = fields.One2many(
        comodel_name="l10n_br_cte.modal.aereo.peri", related="document_id.cte40_peri"
    )

    # Campos do Modal Aquaviario
    modal_aquaviario_id = fields.Many2one(
        comodel_name="l10n_br_cte.modal.aquav",
        related="document_id.modal_aquaviario_id",
    )

    cte40_vPrest = fields.Monetary(related="document_id.cte40_vPrest")

    cte40_vAFRMM = fields.Monetary(related="document_id.cte40_vAFRMM")

    cte40_xNavio = fields.Char(related="document_id.cte40_xNavio")

    cte40_nViag = fields.Char(related="document_id.cte40_nViag")

    cte40_direc = fields.Selection(related="document_id.cte40_direc")

    cte40_irin = fields.Char(related="document_id.cte40_irin")

    cte40_tpNav = fields.Selection(related="document_id.cte40_tpNav")

    cte40_balsa = fields.One2many(
        comodel_name="l10n_br_cte.modal.aquav.balsa",
        related="document_id.cte40_balsa",
    )

    # Campos do Modal Dutoviario
    modal_dutoviario_id = fields.Many2one(
        comodel_name="l10n_br_cte.modal.duto",
        related="document_id.modal_dutoviario_id",
    )

    cte40_dIni = fields.Date(related="document_id.cte40_dIni")

    cte40_dFim = fields.Date(related="document_id.cte40_dFim")

    cte40_vTar = fields.Float(related="document_id.cte40_vTar")

    # Campos do Modal Ferroviario
    modal_ferroviario_id = fields.Many2one(
        comodel_name="l10n_br_cte.modal.ferrov",
        related="document_id.modal_ferroviario_id",
    )

    cte40_tpTraf = fields.Selection(related="document_id.cte40_tpTraf")

    cte40_fluxo = fields.Char(related="document_id.cte40_fluxo")

    cte40_vFrete = fields.Monetary(related="document_id.cte40_vFrete")

    cte40_respFat = fields.Selection(related="document_id.cte40_respFat")

    cte40_ferrEmi = fields.Selection(related="document_id.cte40_ferrEmi")

    cte40_ferroEnv = fields.Many2many(related="document_id.cte40_ferroEnv")

    # Campos do Modal rodoviario
    modal_rodoviario_id = fields.Many2one(
        comodel_name="l10n_br_cte.modal.rodo",
        related="document_id.modal_rodoviario_id",
    )

    cte40_RNTRC = fields.Char(related="document_id.cte40_RNTRC")

    cte40_occ = fields.One2many(
        comodel_name="l10n_br_cte.modal.rodo.occ", related="document_id.cte40_occ"
    )

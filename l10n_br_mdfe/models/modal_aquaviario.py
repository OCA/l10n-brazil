# Copyright 2023 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields

from odoo.addons.spec_driven_model.models import spec_models

from ..constants.modal import MDFE_MODAL_HARBORS


class MDFeModalAquaviario(spec_models.StackedModel):
    _name = "l10n_br_mdfe.modal.aquaviario"
    _inherit = "mdfe.30.aquav"
    _stacked = "mdfe.30.aquav"
    _binding_module = "nfelib.mdfe.bindings.v3_0.mdfe_modal_aquaviario_v3_00"
    _field_prefix = "mdfe30_"
    _schema_name = "mdfe"
    _schema_version = "3.0.0"
    _odoo_module = "l10n_br_mdfe"
    _spec_module = (
        "odoo.addons.l10n_br_mdfe_spec.models.v3_0.mdfe_modal_aquaviario_v3_00"
    )
    _spec_tab_name = "MDFe"
    _mdfe_search_keys = ["mdfe30_irin", "mdfe30_cEmbar", "mdfe30_nViag"]
    _description = "Modal Aquaviário MDFe"

    document_id = fields.Many2one(comodel_name="l10n_br_fiscal.document")

    mdfe30_irin = fields.Char(related="document_id.mdfe30_irin")

    mdfe30_cEmbar = fields.Char(related="document_id.mdfe30_cEmbar")

    mdfe30_xEmbar = fields.Char(related="document_id.mdfe30_xEmbar")

    mdfe30_nViag = fields.Char(related="document_id.mdfe30_nViag")

    mdfe30_prtTrans = fields.Char(related="document_id.mdfe30_prtTrans")

    mdfe30_tpNav = fields.Selection(related="document_id.mdfe30_tpNav")

    mdfe30_infTermCarreg = fields.One2many(related="document_id.mdfe30_infTermCarreg")

    mdfe30_infTermDescarreg = fields.One2many(
        related="document_id.mdfe30_infTermDescarreg"
    )

    mdfe30_infEmbComb = fields.One2many(related="document_id.mdfe30_infEmbComb")

    mdfe30_infUnidCargaVazia = fields.One2many(
        related="document_id.mdfe30_infUnidCargaVazia"
    )

    mdfe30_infUnidTranspVazia = fields.One2many(
        related="document_id.mdfe30_infUnidTranspVazia"
    )

    mdfe30_tpEmb = fields.Char(compute="_compute_mdfe30_tpEmb")

    mdfe30_cPrtEmb = fields.Char(compute="_compute_boarding_landing_point")

    mdfe30_cPrtDest = fields.Char(compute="_compute_boarding_landing_point")

    @api.depends("document_id.mdfe30_tpEmb")
    def _compute_mdfe30_tpEmb(self):
        for record in self:
            record.mdfe30_tpEmb = record.document_id.mdfe30_tpEmb

    @api.depends("document_id.mdfe30_cPrtEmb", "document_id.mdfe30_cPrtDest")
    def _compute_boarding_landing_point(self):
        for record in self:
            record.mdfe30_cPrtEmb = record.document_id.mdfe30_cPrtEmb
            record.mdfe30_cPrtDest = record.document_id.mdfe30_cPrtDest


class MDFeModalAquaviarioCarregamento(spec_models.SpecModel):
    _name = "l10n_br_mdfe.modal.aquaviario.carregamento"
    _inherit = "mdfe.30.inftermcarreg"
    _binding_module = "nfelib.mdfe.bindings.v3_0.mdfe_modal_aquaviario_v3_00"
    _description = "Carregamento no Modal Aquaviário MDFe"

    document_id = fields.Many2one(comodel_name="l10n_br_fiscal.document")

    loading_harbor = fields.Selection(
        selection=MDFE_MODAL_HARBORS, string="Loading Harbor", required=True
    )

    mdfe30_cTermCarreg = fields.Char(compute="_compute_loading_harbor")

    mdfe30_xTermCarreg = fields.Char(compute="_compute_loading_harbor")

    @api.depends("loading_harbor")
    def _compute_loading_harbor(self):
        for record in self:
            record.mdfe30_cTermCarreg = record.loading_harbor
            record.mdfe30_xTermCarreg = dict(
                self._fields["loading_harbor"].selection
            ).get(record.loading_harbor)


class MDFeModalAquaviarioDescarregamento(spec_models.SpecModel):
    _name = "l10n_br_mdfe.modal.aquaviario.descarregamento"
    _inherit = "mdfe.30.inftermdescarreg"
    _binding_module = "nfelib.mdfe.bindings.v3_0.mdfe_modal_aquaviario_v3_00"
    _description = "Descarregamento no Modal Aquaviário MDFe"

    document_id = fields.Many2one(comodel_name="l10n_br_fiscal.document")

    unloading_harbor = fields.Selection(
        selection=MDFE_MODAL_HARBORS, string="Unloading Harbor", required=True
    )

    mdfe30_cTermDescarreg = fields.Char(compute="_compute_unloading_harbor")

    mdfe30_xTermDescarreg = fields.Char(compute="_compute_unloading_harbor")

    @api.depends("unloading_harbor")
    def _compute_unloading_harbor(self):
        for record in self:
            record.mdfe30_cTermDescarreg = record.unloading_harbor
            record.mdfe30_xTermDescarreg = dict(
                self._fields["unloading_harbor"].selection
            ).get(record.unloading_harbor)


class MDFeModalAquaviarioComboio(spec_models.SpecModel):
    _name = "l10n_br_mdfe.modal.aquaviario.comboio"
    _inherit = "mdfe.30.infembcomb"
    _binding_module = "nfelib.mdfe.bindings.v3_0.mdfe_modal_aquaviario_v3_00"
    _description = "Informações de Comboio no Modal Aquaviário MDFe"

    document_id = fields.Many2one(comodel_name="l10n_br_fiscal.document")

    mdfe30_cEmbComb = fields.Char(required=True, size=10)

    mdfe30_xBalsa = fields.Char(required=True, size=60)


class MDFeModalAquaviarioCargaVazia(spec_models.SpecModel):
    _name = "l10n_br_mdfe.modal.aquaviario.carga.vazia"
    _inherit = "mdfe.30.infunidcargavazia"
    _binding_module = "nfelib.mdfe.bindings.v3_0.mdfe_modal_aquaviario_v3_00"
    _description = "Informações de Carga Vazia no Modal Aquaviário MDFe"

    document_id = fields.Many2one(comodel_name="l10n_br_fiscal.document")

    mdfe30_idUnidCargaVazia = fields.Char(required=True)

    mdfe30_tpUnidCargaVazia = fields.Selection(required=True)


class MDFeModalAquaviarioTranporteVazio(spec_models.SpecModel):
    _name = "l10n_br_mdfe.modal.aquaviario.transporte.vazio"
    _inherit = "mdfe.30.infunidtranspvazia"
    _binding_module = "nfelib.mdfe.bindings.v3_0.mdfe_modal_aquaviario_v3_00"
    _description = "Informações de Transporte Vazio no Modal Aquaviário MDFe"

    document_id = fields.Many2one(comodel_name="l10n_br_fiscal.document")

    mdfe30_idUnidTranspVazia = fields.Char(required=True)

    mdfe30_tpUnidTranspVazia = fields.Selection(required=True)

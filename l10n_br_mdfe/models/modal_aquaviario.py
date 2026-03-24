# Copyright 2023 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields
from odoo.exceptions import UserError

from odoo.addons.spec_driven_model.models import spec_models

from ..constants.modal import MDFE_MODAL_HARBORS


class MDFeModalAquaviario(spec_models.StackedModel):
    _name = "l10n_br_mdfe.modal.aquaviario"
    _inherit = "mdfe.30.aquav"
    _description = "Modal Aquaviário MDFe"

    _mdfe30_odoo_module = (
        "odoo.addons.l10n_br_mdfe_spec.models.v3_0.mdfe_modal_aquaviario_v3_00"
    )
    _mdfe30_binding_module = "nfelib.mdfe.bindings.v3_0.mdfe_modal_aquaviario_v3_00"
    _mdfe30_stacking_mixin = "mdfe.30.aquav"
    _mdfe_search_keys = ["mdfe30_irin", "mdfe30_cEmbar", "mdfe30_nViag"]

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
    _description = "Carregamento no Modal Aquaviário MDFe"
    _mdfe30_binding_module = "nfelib.mdfe.bindings.v3_0.mdfe_modal_aquaviario_v3_00"

    document_id = fields.Many2one(comodel_name="l10n_br_fiscal.document")

    loading_harbor = fields.Selection(selection=MDFE_MODAL_HARBORS, required=True)

    mdfe30_cTermCarreg = fields.Char(compute="_compute_loading_harbor")

    mdfe30_xTermCarreg = fields.Char(compute="_compute_loading_harbor")

    @api.depends("loading_harbor")
    def _compute_loading_harbor(self):
        for record in self:
            record.mdfe30_cTermCarreg = record.loading_harbor
            record.mdfe30_xTermCarreg = dict(
                self._fields["loading_harbor"].selection
            ).get(record.loading_harbor)

    @api.constrains("document_id")
    def _check_maximum_carregamento(self):
        for record in self:
            if record.document_id:
                count = self.search_count([("document_id", "=", record.document_id.id)])
                if count > 5:
                    raise UserError(
                        _(
                            "You can only add up to 5 loading terminals "
                            "for the same MDF-e."
                        )
                    )


class MDFeModalAquaviarioDescarregamento(spec_models.SpecModel):
    _name = "l10n_br_mdfe.modal.aquaviario.descarregamento"
    _inherit = "mdfe.30.inftermdescarreg"
    _description = "Descarregamento no Modal Aquaviário MDFe"
    _mdfe30_binding_module = "nfelib.mdfe.bindings.v3_0.mdfe_modal_aquaviario_v3_00"

    document_id = fields.Many2one(comodel_name="l10n_br_fiscal.document")

    unloading_harbor = fields.Selection(selection=MDFE_MODAL_HARBORS, required=True)

    mdfe30_cTermDescarreg = fields.Char(compute="_compute_unloading_harbor")

    mdfe30_xTermDescarreg = fields.Char(compute="_compute_unloading_harbor")

    @api.depends("unloading_harbor")
    def _compute_unloading_harbor(self):
        for record in self:
            record.mdfe30_cTermDescarreg = record.unloading_harbor
            record.mdfe30_xTermDescarreg = dict(
                self._fields["unloading_harbor"].selection
            ).get(record.unloading_harbor)

    @api.constrains("document_id")
    def _check_maximum_descarregamento(self):
        for record in self:
            if record.document_id:
                count = self.search_count([("document_id", "=", record.document_id.id)])
                if count > 5:
                    raise UserError(
                        _(
                            "You can only add up to 5 unloading terminals "
                            "for the same MDF-e."
                        )
                    )


class MDFeModalAquaviarioComboio(spec_models.SpecModel):
    _name = "l10n_br_mdfe.modal.aquaviario.comboio"
    _inherit = "mdfe.30.infembcomb"
    _description = "Informações de Comboio no Modal Aquaviário MDFe"
    _mdfe30_binding_module = "nfelib.mdfe.bindings.v3_0.mdfe_modal_aquaviario_v3_00"

    document_id = fields.Many2one(comodel_name="l10n_br_fiscal.document")

    mdfe30_cEmbComb = fields.Char(required=True, size=10)

    mdfe30_xBalsa = fields.Char(required=True, size=60)


class MDFeModalAquaviarioCargaVazia(spec_models.SpecModel):
    _name = "l10n_br_mdfe.modal.aquaviario.carga.vazia"
    _inherit = "mdfe.30.infunidcargavazia"
    _description = "Informações de Carga Vazia no Modal Aquaviário MDFe"
    _mdfe30_binding_module = "nfelib.mdfe.bindings.v3_0.mdfe_modal_aquaviario_v3_00"

    document_id = fields.Many2one(comodel_name="l10n_br_fiscal.document")

    mdfe30_idUnidCargaVazia = fields.Char(required=True)

    mdfe30_tpUnidCargaVazia = fields.Selection(required=True)


class MDFeModalAquaviarioTranporteVazio(spec_models.SpecModel):
    _name = "l10n_br_mdfe.modal.aquaviario.transporte.vazio"
    _inherit = "mdfe.30.infunidtranspvazia"
    _description = "Informações de Transporte Vazio no Modal Aquaviário MDFe"
    _mdfe30_binding_module = "nfelib.mdfe.bindings.v3_0.mdfe_modal_aquaviario_v3_00"

    document_id = fields.Many2one(comodel_name="l10n_br_fiscal.document")

    mdfe30_idUnidTranspVazia = fields.Char(required=True)

    mdfe30_tpUnidTranspVazia = fields.Selection(required=True)

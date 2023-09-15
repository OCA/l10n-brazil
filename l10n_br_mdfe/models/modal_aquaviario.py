# Copyright 2023 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from nfelib.mdfe.bindings.v3_0.mdfe_modal_aquaviario_v3_00 import Aquav

from odoo import api, fields

from odoo.addons.spec_driven_model.models import spec_models

from ..constants.modal import MDFE_MODAL_HARBORS


class MDFeModalAquaviario(spec_models.SpecModel):
    _name = "l10n_br_mdfe.modal.aquaviario"
    _inherit = "mdfe.30.aquav"
    _mdfe_search_keys = ["mdfe30_irin", "mdfe30_cEmbar", "mdfe30_nViag"]

    mdfe30_infTermCarreg = fields.One2many(
        comodel_name="l10n_br_mdfe.modal.aquaviario.carregamento"
    )

    mdfe30_infTermDescarreg = fields.One2many(
        comodel_name="l10n_br_mdfe.modal.aquaviario.descarregamento"
    )

    mdfe30_infEmbComb = fields.One2many(
        comodel_name="l10n_br_mdfe.modal.aquaviario.comboio"
    )

    mdfe30_infUnidCargaVazia = fields.One2many(
        comodel_name="l10n_br_mdfe.modal.aquaviario.carga.vazia"
    )

    mdfe30_infUnidTranspVazia = fields.One2many(
        comodel_name="l10n_br_mdfe.modal.aquaviario.transporte.vazio"
    )


class MDFeModalAquaviarioCarregamento(spec_models.SpecModel):
    _name = "l10n_br_mdfe.modal.aquaviario.carregamento"
    _inherit = "mdfe.30.inftermcarreg"

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

    @api.model
    def export_fields(self):
        if len(self) > 1:
            return self.export_fields_multi()

        return Aquav.InfTermCarreg(
            cTermCarreg=self.mdfe30_cTermCarreg,
            xTermCarreg=self.mdfe30_xTermCarreg,
        )

    @api.model
    def export_fields_multi(self):
        return [record.export_fields() for record in self]


class MDFeModalAquaviarioDescarregamento(spec_models.SpecModel):
    _name = "l10n_br_mdfe.modal.aquaviario.descarregamento"
    _inherit = "mdfe.30.inftermdescarreg"

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

    @api.model
    def export_fields(self):
        if len(self) > 1:
            return self.export_fields_multi()

        return Aquav.InfTermDescarreg(
            cTermDescarreg=self.mdfe30_cTermDescarreg,
            xTermDescarreg=self.mdfe30_xTermDescarreg,
        )

    @api.model
    def export_fields_multi(self):
        return [record.export_fields() for record in self]


class MDFeModalAquaviarioComboio(spec_models.SpecModel):
    _name = "l10n_br_mdfe.modal.aquaviario.comboio"
    _inherit = "mdfe.30.infembcomb"

    document_id = fields.Many2one(comodel_name="l10n_br_fiscal.document")

    mdfe30_cEmbComb = fields.Char(required=True)

    mdfe30_xBalsa = fields.Char(required=True)

    @api.model
    def export_fields(self):
        if len(self) > 1:
            return self.export_fields_multi()

        return Aquav.InfEmbComb(
            cEmbComb=self.mdfe30_cEmbComb,
            xBalsa=self.mdfe30_xBalsa,
        )

    @api.model
    def export_fields_multi(self):
        return [record.export_fields() for record in self]


class MDFeModalAquaviarioCargaVazia(spec_models.SpecModel):
    _name = "l10n_br_mdfe.modal.aquaviario.carga.vazia"
    _inherit = "mdfe.30.infunidcargavazia"

    document_id = fields.Many2one(comodel_name="l10n_br_fiscal.document")

    mdfe30_idUnidCargaVazia = fields.Char(required=True)

    mdfe30_tpUnidCargaVazia = fields.Selection(required=True)

    @api.model
    def export_fields(self):
        if len(self) > 1:
            return self.export_fields_multi()

        return Aquav.InfUnidCargaVazia(
            idUnidCargaVazia=self.mdfe30_idUnidCargaVazia,
            tpUnidCargaVazia=self.mdfe30_tpUnidCargaVazia,
        )

    @api.model
    def export_fields_multi(self):
        return [record.export_fields() for record in self]


class MDFeModalAquaviarioTranporteVazio(spec_models.SpecModel):
    _name = "l10n_br_mdfe.modal.aquaviario.transporte.vazio"
    _inherit = "mdfe.30.infunidtranspvazia"

    document_id = fields.Many2one(comodel_name="l10n_br_fiscal.document")

    mdfe30_idUnidTranspVazia = fields.Char(required=True)

    mdfe30_tpUnidTranspVazia = fields.Selection(required=True)

    @api.model
    def export_fields(self):
        if len(self) > 1:
            return self.export_fields_multi()

        return Aquav.InfUnidTranspVazia(
            idUnidTranspVazia=self.mdfe30_idUnidTranspVazia,
            tpUnidTranspVazia=self.mdfe30_tpUnidTranspVazia,
        )

    @api.model
    def export_fields_multi(self):
        return [record.export_fields() for record in self]

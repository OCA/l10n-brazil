from nfelib.nfse.bindings.v1_0.dps_v1_00 import Dps

from odoo import fields, api
from odoo.addons.spec_driven_model.models import spec_models

class L10nBrFiscalDocument(spec_models.SpecModel):
    _name = "l10n_br_fiscal.document"
    _inherit = [
        "l10n_br_fiscal.document",
        #        "nfse.10.tcinfnfse",
        "nfse.10.tcdps",
        "nfse.10.tcinfdps",
    ]

    _nfse10_odoo_module = "odoo.addons.l10n_br_nfse_spec.models.v1_0.tipos_complexos_v1_00"
    _nfse10_binding_module = "nfelib.nfse.bindings.v1_0.tipos_complexos_v1_00"
    _nfse10_binding_type = "TcinfDps" #Tcdps"
#    _nfse10_binding_module = "nfelib.nfse.bindings.v1_0.dps_v1_00"
#    _nfse10_binding_type = "Dps" #Tcdps"

    nfse10_infDPS = fields.Many2one("l10n_br_fiscal.document", compute="_compute_nfse10_self")

    nfse10_Id = fields.Char(compute="_compute_nfse10_id")
    nfse10_tpAmb = fields.Selection(related="company_id.nfse_environment")
    nfse10_dhEmi = fields.Char(compute="_compute_nfse10_dates")
    nfse10_verAplic = fields.Char(default="Odoo OCA")
    nfse10_serie = fields.Char(related="document_serie")
    nfse10_nDPS = fields.Char(related="document_number")
    nfse10_dCompet = fields.Char(compute="_compute_nfse10_dates")
    nfse10_tpEmit = fields.Selection(default="1")
    nfse10_cLocEmi = fields.Char(related="company_id.partner_id.city_id.ibge_code")

    nfse10_prest = fields.Many2one("res.company", related="company_id")
    nfse10_toma = fields.Many2one("res.partner", related="partner_id")

    nfse10_serv = fields.Many2one("l10n_br_fiscal.document.line", compute="_compute_nfse10_serv_valores")
    nfse10_valores = fields.Many2one("l10n_br_fiscal.document.line", compute="_compute_nfse10_serv_valores")

    def _compute_nfse10_self(self):
        for rec in self:
            rec.nfse10_infDPS = rec.id

    @api.depends("document_key")
    def _compute_nfse10_id(self):
        for rec in self:
            rec.nfse10_Id = f"DPS{rec.document_key}" if rec.document_key else False

    @api.depends("document_date", "date_in_out")
    def _compute_nfse10_dates(self):
        for rec in self:
            if rec.document_date:
                # Timezone offset applied for standard spec mapping
                rec.nfse10_dhEmi = rec.document_date.strftime("%Y-%m-%dT%H:%M:%S-03:00")
                rec.nfse10_dCompet = rec.document_date.strftime("%Y-%m-%d")
            else:
                rec.nfse10_dhEmi = False
                rec.nfse10_dCompet = False

    @api.depends("fiscal_line_ids")
    def _compute_nfse10_serv_valores(self):
        for rec in self:
            if rec.fiscal_line_ids:
                rec.nfse10_serv = rec.fiscal_line_ids[0].id
                rec.nfse10_valores = rec.fiscal_line_ids[0].id
            else:
                rec.nfse10_serv = False
                rec.nfse10_valores = False

    def _export_many2one(self, field_name, xsd_required, class_obj=None):
        if field_name == "nfse10_infDPS":
            return self._build_binding(class_name=class_obj._fields[field_name].comodel_name)
        return super()._export_many2one(field_name, xsd_required, class_obj)

    def import_binding_nfse(self, binding, edoc_type="in", dry_run=False):
        if hasattr(binding, "DPS"):
            binding = binding.DPS
        document = (
            self.env["nfse.10.tcdps"]
            .with_context(tracking_disable=True, edoc_type=edoc_type)
            .build_from_binding("nfse", "10", binding.infDPS, dry_run=dry_run)
        )
        return document

    @api.constrains("document_key")
    def _check_key(self):  # TODO required??
        """
        Bypass the 44-digit ChaveEdoc validation for NFS-e Nacional.
        DPS uses 42 digits and NFS-e uses 50 digits, which breaks the standard validation.
        """
        nfse_nacional_docs = self.filtered(
            lambda r: r.document_type_id and r.document_type_id.code == "SE"
        )
        other_docs = self - nfse_nacional_docs

        # Only call the strict l10n_br_fiscal validation on NFe/CTe/MDFe
        if other_docs:
            super(L10nBrFiscalDocument, other_docs)._check_key()

    def _serialize(self, edocs):
        edocs = super()._serialize(edocs)
        for record in self.with_context(lang="pt_BR").filtered(
#            filter_processador_edoc_cte
            # TODO make t compat with Focus etc...
            lambda r: r.document_type_id and r.document_type_id.code == "SE"
        ):
            inf_dps = record._build_binding("nfse", "10")
            nfse = Dps(infDPS=inf_dps, signature=None)
            edocs.append(nfse)
        return edocs


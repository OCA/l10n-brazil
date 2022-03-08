# Copyright 2020 Akretion (Renato Lima <renato.lima@akretion.com>)
# Copyright 2020 KMEE (Luis Felipe Mileo <mileo@kmee.com.br>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    MODELO_FISCAL_01,
    MODELO_FISCAL_04,
    MODELO_FISCAL_CFE,
    MODELO_FISCAL_CTE,
    MODELO_FISCAL_CUPOM_FISCAL_ECF,
    MODELO_FISCAL_NFCE,
    MODELO_FISCAL_NFE,
    MODELO_FISCAL_RL,
)
from odoo.addons.spec_driven_model.models import spec_models


class NFeRelated(spec_models.StackedModel):
    _name = "l10n_br_fiscal.document.related"
    _inherit = ["l10n_br_fiscal.document.related", "nfe.40.nfref"]
    _stacked = "nfe.40.nfref"
    _field_prefix = "nfe40_"
    _schema_name = "nfe"
    _schema_version = "4.0.0"
    _odoo_module = "l10n_br_nfe"
    _spec_module = "odoo.addons.l10n_br_nfe_spec.models.v4_00.leiauteNFe"
    _spec_tab_name = "NFe"
    _stack_skip = "nfe40_NFref_ide_id"
    # all m2o below this level will be stacked even if not required:
    _rec_name = "nfe40_refNFe"

    produtor_partner_id = fields.Many2one(
        comodel_name="res.partner", string="Produtor", required=False
    )

    nfe40_choice4 = fields.Selection(
        compute="_compute_nfe_data",
        inverse="_inverse_nfe40_choice4",
    )

    nfe40_refNFe = fields.Char(
        compute="_compute_nfe_data",
        inverse="_inverse_nfe40_refNFe",
    )

    nfe40_refCTe = fields.Char(
        compute="_compute_nfe_data",
        inverse="_inverse_nfe40_refCTe",
    )

    nfe40_choice5 = fields.Selection(
        selection=[("nfe40_CNPJ", "CNPJ"), ("nfe40_CPF", "CPF")],
        string="CNPJ/CPF do Produtor",
    )

    nfe40_mod = fields.Selection(
        selection=[
            ("2B", "2B"),
            ("2C", "2C"),
            ("2D", "2D"),
            ("01", "01"),
            ("02", "02"),
            ("04", "04"),
        ],
    )

    # TODO
    # nfe40_refNF = fields.Many2one(
    #     compute='_compute_nfe_data',
    #     inverse='_inverse_nfe40_refNF',
    #     store=True,
    # )
    #
    # nfe40_refNFP = fields.Many2one(
    #     compute='_compute_nfe_data',
    #     inverse='_inverse_nfe40_refNFP',
    #     store=True,
    # )
    #
    # nfe40_refECF = fields.Many2one(
    #     compute='_compute_nfe_data',
    #     inverse='_inverse_nfe40_refECF',
    #     store=True,
    # )

    @api.depends(
        "document_type_id",
        "state_id",
        "document_date",
        "cnpj_cpf",
        "inscr_est",
        "document_serie",
        "document_number",
        "cpfcnpj_type",
    )
    def _compute_nfe_data(self):
        """Set schema data which are not just related fields"""
        for rec in self:
            if rec.document_type_id:
                document = rec.document_related_id
                if rec.document_type_id.code in (
                    MODELO_FISCAL_NFE,
                    MODELO_FISCAL_NFCE,
                    MODELO_FISCAL_CFE,
                ):
                    rec.nfe40_choice4 = "nfe40_refNFe"
                    rec.nfe40_refNFe = document.document_key
                elif rec.document_type_id.code == MODELO_FISCAL_CTE:
                    rec.nfe40_choice4 = "nfe40_refCTe"
                    rec.nfe40_refCTe = document.document_key
                else:
                    if rec.document_type_id.code == MODELO_FISCAL_RL:
                        rec.nfe40_choice4 = "nfe40_refNFP"
                        rec._prepare_NFP_values()
                    elif rec.document_type_id.code == MODELO_FISCAL_CUPOM_FISCAL_ECF:
                        rec.nfe40_choice4 = "nfe40_refECF"
                    elif rec.document_type_id.code in (
                        MODELO_FISCAL_01,
                        MODELO_FISCAL_04,
                    ):
                        rec.nfe40_choice4 = "nfe40_refNF"

                    rec.nfe40_cUF = rec.state_id.ibge_code
                    rec.nfe40_AAMM = (
                        fields.Datetime.from_string(rec.document_date).strftime("%y%m")
                        if rec.document_date
                        else ""
                    )
                    if rec.cpfcnpj_type == "cpf":
                        rec.nfe40_choice5 = "nfe40_CPF"
                        rec.nfe40_CPF = rec.cnpj_cpf
                        rec.nfe40_CNPJ = ""
                    else:
                        rec.nfe40_choice5 = "nfe40_CNPJ"
                        rec.nfe40_CNPJ = rec.cnpj_cpf
                        rec.nfe40_CPF = ""

                    rec.nfe40_IE = rec.inscr_est
                    rec.nfe40_mod = (
                        rec.document_type_id.code
                        if (rec.document_type_id.code, rec.document_type_id.code)
                        in rec._fields["nfe40_mod"].selection
                        else ""
                    )
                    rec.nfe40_serie = rec.document_serie
                    rec.nfe40_nNF = rec.document_number

    def _inverse_nfe40_choice4(self):
        for rec in self:
            if rec.nfe40_choice4 == "nfe40_refNFe":
                rec.document_type_id = self.env.ref("l10n_br_fiscal.document_55")
            elif rec.nfe40_choice4 == "nfe40_refNFP":
                rec.document_type_id = self.env.ref("l10n_br_fiscal.document_04")

    def _inverse_nfe40_refNFe(self):
        for rec in self:
            if rec.nfe40_refNFe:
                rec.document_key = rec.nfe40_refNFe

    def _inverse_nfe40_refCTe(self):
        for record in self:
            if record.nfe40_refCTe:
                record.document_key = record.nfe40_refCTe

    def _export_fields(self, xsd_fields, class_obj, export_dict):
        if class_obj._name == "nfe.40.nfref":
            xsd_fields = [
                f
                for f in xsd_fields
                if f not in [i[0] for i in class_obj._fields["nfe40_choice4"].selection]
            ]
            xsd_fields += [self.nfe40_choice4]
        return super()._export_fields(xsd_fields, class_obj, export_dict)

    def _prepare_NFP_values(self):
        self.state_id = self.produtor_partner_id.state_id or self.state_id
        self.cpfcnpj_type = (
            "cnpj" if self.produtor_partner_id.is_company else "cpf"
        ) or self.cpfcnpj_type
        self.cnpj_cpf = self.produtor_partner_id.cnpj_cpf or self.cnpj_cpf
        self.inscr_est = self.produtor_partner_id.inscr_est or self.inscr_est

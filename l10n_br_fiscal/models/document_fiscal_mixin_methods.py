# Copyright (C) 2019  Renato Lima - Akretion <renato.lima@akretion.com.br>
# Copyright (C) 2020  Luis Felipe Mileo - KMEE <mileo@kmee.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, models, _
from odoo.exceptions import UserError


class FiscalDocumentMixinMethods(models.AbstractModel):
    _name = 'l10n_br_fiscal.document.mixin.methods'
    _description = 'Document Fiscal Mixin Methods'

    @api.model
    def fields_view_get(
            self, view_id=None, view_type="form", toolbar=False, submenu=False):

        model_view = super().fields_view_get(
            view_id, view_type, toolbar, submenu
        )
        return model_view  # TO REMOVE

        # if view_type == "form":
        #     fiscal_view = self.env.ref("l10n_br_fiscal.document_fiscal_mixin_form")
        #
        #     doc = etree.fromstring(model_view.get("arch"))
        #
        #     for fiscal_node in doc.xpath("//group[@name='l10n_br_fiscal']"):
        #         sub_view_node = etree.fromstring(fiscal_view["arch"])
        #
        #         from odoo.osv.orm import setup_modifiers
        #         setup_modifiers(fiscal_node)
        #         try:
        #             fiscal_node.getparent().replace(fiscal_node, sub_view_node)
        #             model_view["arch"] = etree.tostring(doc, encoding="unicode")
        #         except ValueError:
        #             return model_view
        #
        # return model_view

    @api.multi
    def _prepare_br_fiscal_dict(self, default=False):
        self.ensure_one()
        fields = self.env["l10n_br_fiscal.document.mixin"]._fields.keys()

        # we now read the record fiscal fields except the m2m tax:
        vals = self._convert_to_write(self.read(fields)[0])

        # this will force to create a new fiscal document line:
        vals['fiscal_document_id'] = False

        if default:  # in case you want to use new rather than write later
            return {"default_%s" % (k,): vals[k] for k in vals.keys()}
        return vals

    @api.onchange('company_id')
    def _onchange_company_id(self):
        if self.company_id:
            self.company_legal_name = self.company_id.legal_name
            self.company_name = self.company_id.name
            self.company_cnpj_cpf = self.company_id.cnpj_cpf
            self.company_inscr_est = self.company_id.inscr_est
            self.company_inscr_mun = self.company_id.inscr_mun
            self.company_suframa = self.company_id.suframa
            self.company_cnae_main_id = self.company_id.cnae_main_id
            self.company_tax_framework = self.company_id.tax_framework

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        if self.partner_id:
            self.partner_legal_name = self.partner_id.legal_name
            self.partner_name = self.partner_id.name
            self.partner_cnpj_cpf = self.partner_id.cnpj_cpf
            self.partner_inscr_est = self.partner_id.inscr_est
            self.partner_inscr_mun = self.partner_id.inscr_mun
            self.partner_suframa = self.partner_id.suframa
            self.partner_cnae_main_id = self.partner_id.cnae_main_id
            self.partner_tax_framework = self.partner_id.tax_framework

    @api.onchange('fiscal_operation_id')
    def _onchange_fiscal_operation_id(self):
        if self.fiscal_operation_id:
            self.operation_name = self.fiscal_operation_id.name
            self.comment_ids |= self.fiscal_operation_id.comment_ids

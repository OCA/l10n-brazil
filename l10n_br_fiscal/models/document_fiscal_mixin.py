# Copyright (C) 2019  Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from lxml import etree
from odoo import api, fields, models

from ..constants.fiscal import (
    TAX_FRAMEWORK,
    FISCAL_IN_OUT)


class DocumentFiscalMixin(models.AbstractModel):
    _name = 'l10n_br_fiscal.document.mixin'
    _description = 'Document Fiscal Mixin'

    operation_id = fields.Many2one(
        comodel_name='l10n_br_fiscal.operation',
        domain="[('state', '=', 'approved')]",
        string='Operation')

    operation_type = fields.Selection(
        selection=FISCAL_IN_OUT,
        related='operation_id.operation_type',
        string='Operation Type',
        readonly=True)

    @api.model
    def fields_view_get(self, view_id=None, view_type='form',
                        toolbar=False, submenu=False):

        model_view = super(DocumentFiscalMixin, self).fields_view_get(
            view_id, view_type, toolbar, submenu)

        if view_type == 'form':
            fiscal_view = self.env.ref(
                'l10n_br_fiscal.document_fiscal_mixin_form')

            doc = etree.fromstring(model_view.get('arch'))

            for fiscal_node in doc.xpath("//group[@id='l10n_br_fiscal']"):
                sub_view_node = etree.fromstring(fiscal_view['arch'])

                try:
                    fiscal_node.getparent().replace(fiscal_node, sub_view_node)
                    model_view['arch'] = etree.tostring(doc, encoding='unicode')
                except ValueError:
                    return model_view

        return model_view

# Copyright (C) 2019  Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields, api
from odoo.osv import expression


class DocumentLineAbstract(models.AbstractModel):
    _name = 'fiscal.document.line.abstract'
    _description = 'Fiscal Document Line Abstract'

    document_id = fields.Many2one(
        comodel_name='fiscal.document.abstract',
        string='Document')

    operation_id = fields.Many2one(
        comodel_name='fiscal.operation.line',
        string='Partner')

    company_id = fields.Many2one(
        comodel_name='res.company',
        related='operation_id.company_id',
        string='Company')

    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product')

    uom_id = fields.Many2one(
        comodel_name='uom.uom',
        string='UOM')

    quantity = fields.Float(
        string='Product')

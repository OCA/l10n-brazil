# -*- encoding: utf-8 -*-

from openerp import models, fields


class Product(models.Model):

    _inherit = 'product.template'

    fci_ids = fields.Many2many('l10n_br.fci', 'product_id', 'fci_id', 'fci_product_rel', string='Products')

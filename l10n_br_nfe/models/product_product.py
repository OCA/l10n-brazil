# Copyright 2020 Akretion (Raphaël Valyi <raphael.valyi@akretion.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
# The generateDS prod mixin (prod XML tag) cannot be injected in
# the product.product object because the tag includes attributes from the
# Odoo fiscal document line. So a part of the mapping is done
# in the fiscal document line:
# from Odoo -> XML by using related fields/_compute
# from XML -> Odoo by overriding the product create method


from odoo import api, models


class ProductProduct(models.Model):
    _inherit = 'product.product'
    _nfe_search_keys = ['default_code', 'barcode']

    @api.model
    def create(self, values):
        parent_dict = self._context.get('parent_dict', {})
        if parent_dict.get('nfe40_xProd'):
            values['name'] = parent_dict['nfe40_xProd']

        # Price Unit
        if parent_dict.get('nfe40_vUnCom'):
            values['standard_price'] = parent_dict.get('nfe40_vUnCom')
            values['list_price'] = parent_dict.get('nfe40_vUnCom')

        # Barcode
        if (parent_dict.get('nfe40_cEAN')
                and parent_dict['nfe40_cEAN'] != 'SEM GTIN'):
            values['barcode'] = parent_dict['nfe40_cEAN']

        # NCM
        if parent_dict.get('nfe40_NCM'):
            ncm = self.env['l10n_br_fiscal.ncm'].search(
                [('code_unmasked', '=', parent_dict['nfe40_NCM'])], limit=1)

            values['ncm_id'] = ncm.id

            if not ncm:  # FIXME should not happen with prod data
                ncm = self.env['l10n_br_fiscal.ncm'].sudo().create(
                    {'name': parent_dict['nfe40_NCM'],
                     'code': parent_dict['nfe40_NCM']})
                values['ncm_id'] = ncm.id
        product = super().create(values)
        product.product_tmpl_id._onchange_ncm_id()
        return product

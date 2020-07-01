# Copyright 2019 Akretion (Raphaël Valyi <raphael.valyi@akretion.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, models


class ProductProduct(models.Model):
    _inherit = "product.product"
    _nfe_search_keys = ['default_code', 'barcode']

    @api.model
    def create(self, vals):
        print("CREATE PRODUCT FROM NFE", vals, self._context)
        parent_dict = self._context.get('parent_dict')
        if parent_dict:
            vals['standard_price'] = parent_dict.get('nfe40_vUnCom')
            vals['list_price'] = parent_dict.get('nfe40_vUnCom')
            if parent_dict.get('nfe40_cEAN') and\
                    parent_dict['nfe40_cEAN'] != 'SEM GTIN':
                vals['barcode'] = parent_dict['nfe40_cEAN']
            if parent_dict.get('nfe40_NCM'):
                raw_ncm = parent_dict['nfe40_NCM']
                ncm = "%s.%s.%s" % (raw_ncm[0:4], raw_ncm[4:6], raw_ncm[6:8])
                ncm_ids = self.env['l10n_br_fiscal.ncm'].search(
                    [('code', '=', ncm)])
                if not ncm_ids:
                    ncm = "%s.%s." % (raw_ncm[0:4], raw_ncm[4:6])
                    ncm_ids = self.env['l10n_br_fiscal.ncm'].search(
                        [('code', '=', ncm)])
                if ncm_ids:
                    vals['ncm_id'] = ncm_ids[0].id
                else: # FIXME should not happen with prod data
                    ncm = self.env['l10n_br_fiscal.ncm'].sudo().create(
                        {'name': parent_dict['nfe40_NCM'],
                         'code': parent_dict['nfe40_NCM']})
                    vals['ncm_id'] = ncm.id
            print("VALS, NCM_IDS", vals, ncm_ids)
        product = super().create(vals)
        product.product_tmpl_id._onchange_ncm_id()
        return product

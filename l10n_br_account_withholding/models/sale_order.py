# -*- coding: utf-8 -*-
# © 2016 KMEE(http://www.kmee.com.br)
#   @author Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from openerp import models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _witholding_map(self, cr, uid, **kwargs):
        result = {}
        obj_partner = self.pool.get('res.partner').browse(
            cr, uid, kwargs.get('partner_id', False))
        obj_company = self.pool.get('res.company').browse(
            cr, uid, kwargs.get('company_id', False))

        result['issqn_wh'] = obj_company.issqn_wh or \
            obj_partner.partner_fiscal_type_id.issqn_wh
        result['inss_wh'] = obj_company.inss_wh or \
            obj_partner.partner_fiscal_type_id.inss_wh
        result['pis_wh'] = obj_company.pis_wh or \
            obj_partner.partner_fiscal_type_id.pis_wh
        result['cofins_wh'] = obj_company.cofins_wh or \
            obj_partner.partner_fiscal_type_id.cofins_wh
        result['csll_wh'] = obj_company.csll_wh or \
            obj_partner.partner_fiscal_type_id.csll_wh
        result['irrf_wh'] = obj_company.irrf_wh or \
            obj_partner.partner_fiscal_type_id.irrf_wh

        return result

    def _prepare_invoice(self, cr, uid, order, lines, context=None):
        result = super(SaleOrder, self)._prepare_invoice(
            cr, uid, order, lines, context)

        result.update(self._witholding_map(
            cr, uid, partner_id=order.partner_id.id,
            company_id=order.company_id.id))
        print result
        return result

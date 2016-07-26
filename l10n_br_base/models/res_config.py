# -*- coding: utf-8 -*-

from openerp import fields, models
from openerp.tools.safe_eval import safe_eval


class res_config(models.TransientModel):
    _inherit = 'base.config.settings'

    allow_cnpj_multi_ie = fields.Boolean(
        string=u'Permitir o cadastro de Customers com CNPJs iguais',
        default=False,
    )

    def get_default_allow_cnpj_multi_ie(self, cr, uid, fields, context=None):
        icp = self.pool.get('ir.config_parameter')
        return {
            'allow_cnpj_multi_ie': safe_eval(icp.get_param(
                cr, uid, 'l10n_br_base_allow_cnpj_multi_ie', 'False')),
        }

    def set_allow_cnpj_multi_ie(self, cr, uid, ids, context=None):
        config = self.browse(cr, uid, ids[0], context=context)
        icp = self.pool.get('ir.config_parameter')
        icp.set_param(cr, uid, 'l10n_br_base_allow_cnpj_multi_ie',
                      repr(config.allow_cnpj_multi_ie))

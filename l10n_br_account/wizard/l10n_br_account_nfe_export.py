# -*- coding: utf-8 -*-
###############################################################################
#                                                                             #
# Copyright (C) 2009  Renato Lima - Akretion                                  #
#                                                                             #
#This program is free software: you can redistribute it and/or modify         #
#it under the terms of the GNU Affero General Public License as published by  #
#the Free Software Foundation, either version 3 of the License, or            #
#(at your option) any later version.                                          #
#                                                                             #
#This program is distributed in the hope that it will be useful,              #
#but WITHOUT ANY WARRANTY; without even the implied warranty of               #
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the                #
#GNU Affero General Public License for more details.                          #
#                                                                             #
#You should have received a copy of the GNU Affero General Public License     #
#along with this program.  If not, see <http://www.gnu.org/licenses/>.        #
###############################################################################

from openerp.osv import orm, fields


class l10n_br_account_nfe_export(orm.TransientModel):
    """ Exportar Nota Fiscal Eletrônica """
    _name = 'l10n_br_account.nfe_export'
    _inherit = 'l10n_br_account.nfe_export_invoice'
    _columns = {
        'company_id': fields.many2one('res.company', 'Company'),
        'import_status_draft': fields.boolean("Importar NFs com status "
                                              "em rascunho"),
        'nfe_export_result': fields.one2many(
            'l10n_br_account.nfe_export_result', 'wizard_id',
            'NFe Export Result'),
    }
    _defaults = {
        'company_id': lambda self, cr, uid,
            c: self.pool.get('res.company')._company_default_get(
                cr, uid, 'account.invoice', context=c),
    }

    def _get_invoice_ids(self, cr, uid, data, context=None):

        if not context:
            context = {}

        return self.pool.get('account.invoice').search(cr, uid,
            [('state', '=', 'sefaz_export'),
             ('nfe_export_date', '=', False),
             ('company_id', '=', data['company_id'][0]),
             ('issuer', '=', '0')])


class l10n_br_account_nfe_export_result(orm.TransientModel):
    _name = 'l10n_br_account.nfe_export_result'
    _inherit = 'l10n_br_account.nfe_export_invoice_result'
    _columns = {
        'wizard_id': fields.many2one(
            'l10n_br_account.nfe_export', 'Wizard ID',
            ondelete='cascade', select=True),
    }

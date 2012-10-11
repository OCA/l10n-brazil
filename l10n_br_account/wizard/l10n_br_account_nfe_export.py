# -*- coding: utf-8 -*-
#################################################################################
#                                                                               #
# Copyright (C) 2009  Renato Lima - Akretion                                    #
#                                                                               #
#This program is free software: you can redistribute it and/or modify           #
#it under the terms of the GNU Affero General Public License as published by    #
#the Free Software Foundation, either version 3 of the License, or              #
#(at your option) any later version.                                            #
#                                                                               #
#This program is distributed in the hope that it will be useful,                #
#but WITHOUT ANY WARRANTY; without even the implied warranty of                 #
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the                  #
#GNU Affero General Public License for more details.                            #
#                                                                               #
#You should have received a copy of the GNU Affero General Public License       #
#along with this program.  If not, see <http://www.gnu.org/licenses/>.          #
#################################################################################

import time
import base64
from osv import osv, fields
from tools.translate import _

from l10n_br_account.sped.nfe.serializer import txt, xml


class l10n_br_account_nfe_export(osv.osv_memory):
    """ Exportar Nota Fiscal Eletrônica """

    _name = "l10n_br_account.nfe_export"
    _description = "Exportação de Nota Fiscal Eletrônica"
    _inherit = "ir.wizard.screen"

    _columns = {
                'name': fields.char('Name', size=255),
                'file': fields.binary('Arquivo', readonly=True),
                'company_id': fields.many2one('res.company', 'Company'),
                'file_type': fields.selection([('xml', 'XML'), ('txt', 'TXT')], 'Tipo do Arquivo'),
                'import_status_draft': fields.boolean('Importar NFs com status em rascunho'),
                'state': fields.selection([('init', 'init'), ('done', 'done')], 'state', readonly=True),
                'nfe_environment': fields.selection([('1', 'Produção'), ('2', 'Homologação')], 'Ambiente'),
    }

    _defaults = {
        'state': 'init',
        'company_id': lambda self, cr, uid, c: self.pool.get('res.company')._company_default_get(cr, uid, 'account.invoice', context=c),
        'file_type': 'txt',
        'import_status_draft': False,
        'nfe_environment': '1',
    }

    def nfe_export(self, cr, uid, ids, context=None):
        data = self.read(cr, uid, ids, [], context=context)[0]

        inv_obj = self.pool.get('account.invoice')
        inv_ids = inv_obj.search(cr, uid, [('state', '=', 'sefaz_export'), ('nfe_export_date', '=', False), ('company_id', '=', data['company_id'][0]), ('own_invoice', '=', True)])
        if not inv_ids:
            raise osv.except_osv(_('Error !'), _("'%s'") % _('Nenhum documento fiscal para exportação!'))
        
        mod = __import__('l10n_br_account.sped.nfe.serializer.' + data['file_type'], 
                             globals(), locals(), data['file_type'])
            
        func = getattr(mod, 'nfe_export')        
        file = func(cr, uid, inv_ids, data['nfe_environment'])
            
        name = 'nfes%s-%s.%s' % (time.strftime('%d-%m-%Y'), self.pool.get('ir.sequence').get(cr, uid, 'nfe.export'), data['file_type'])
        self.write(cr, uid, ids, {'file': base64.b64encode(file), 'state': 'done', 'name': name}, context=context)

        return False

l10n_br_account_nfe_export()
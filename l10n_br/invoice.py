# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution    
#    Copyright (C) 2004-2008 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from osv import osv, fields

##############################################################################
# Fatura (Nota Fiscal) Personalizado
##############################################################################
class account_invoice(osv.osv):
    _inherit = 'account.invoice'
    _columns = {
        'state_nfe': fields.selection([
            ('signed','Assinada'),
            ('authorized','Autorizada'),
            ('canceled','Cancelada'),
            ('denied','Denegada'),
            ('typing','Em Digitação'),
            ('processing','Em processamento na SEFAZ'),
            ('rejected','Rejeitada'),
            ('pending','Transmitida com Pendência'),
            ('validated','Validada')
            ],'Status NFe', select=True, readonly=True),
        'access_key_nfe': fields.char('Chave de Acesso', size=44),
        'fiscal_document_id': fields.many2one('l10n_br.fiscal.document', 'Documento'),
        'cfop_id': fields.many2one('l10n_br.cfop', 'CFOP'),
    }
    
account_invoice()
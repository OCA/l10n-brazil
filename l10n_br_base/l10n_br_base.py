# -*- encoding: utf-8 -*-
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


class L10n_brBaseCity(orm.Model):
    """ Este objeto persite todos os municípios relacionado a um estado.
    No Brasil é necesário em alguns documentos fiscais informar o código
    do IBGE dos município envolvidos da transação.
    """
    _name = 'l10n_br_base.city'
    _description = u'Municipio'
    _columns = {
        'name': fields.char('Nome', size=64, required=True),
        'state_id': fields.many2one('res.country.state', 'Estado',
                                    required=True),
        'ibge_code': fields.char('Codigo IBGE', size=7)
    }

# -*- encoding: utf-8 -*-
###############################################################################
#                                                                             #
# Copyright (C) 2013  Renato Lima - Akretion                                  #
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

from openerp.osv import orm
from openerp.tools.translate import _


def validation(nfe_xml):
    try:
        from pysped.nfe.leiaute import NFe_200, Det_200, NFRef_200, Dup_200
        nfe = NFe_200()
        nfe.get_xml(nfe_xml)
    except ImportError:
        raise orm.except_orm(
            _(u'Erro!'), _(u"Biblioteca PySPED não instalada!"))

   return nfe.validar()


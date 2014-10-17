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

from openerp.addons.l10n_br_account_product.sped.nfe.document import NFe200
from openerp.addons.l10n_br_account_product.sped.nfe.document import NFe310
from openerp.osv import orm


class NFe200(NFe200):

    def __init__(self):
        super(NFe200, self).__init__()

    def validation(self, nfe_xml):
        try:
            from pysped.nfe.leiaute import NFe_200
            nfe = NFe_200()
            nfe.set_xml(nfe_xml)
        except ImportError:
            raise orm.except_orm(
                _(u'Erro!'), _(u"Biblioteca PySPED não instalada!"))
        return nfe.validar()


class NFe310(NFe310):

    def __init__(self):
        super(NFe310, self).__init__()


    def validation(self, nfe_xml):
        try:
            from pysped.nfe.leiaute import NFe_310
            nfe = NFe_310()
            nfe.set_xml(nfe_xml)
        except ImportError:
            raise orm.except_orm(
                _(u'Erro!'), _(u"Biblioteca PySPED não instalada!"))

        return nfe.validar()
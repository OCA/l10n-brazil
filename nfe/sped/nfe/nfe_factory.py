# -*- coding: utf-8 -*-
##############################################################################
#
#    KMEE, KM Enterprising Engineering
#    Copyright (C) 2014 - Michell Stuttgart Faria (<http://www.kmee.com.br>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################


class NfeFactory(object):

    def get_nfe(self, company):
        """
        Retorna objeto NFe de acordo com a versao de NFe em uso no OpenERP
        :param company: objeto res.company
        :return: Objeto Nfe
        """
        if company.nfe_version == '3.10':
            from document import NFe310
            nfe_obj = NFe310()
        else:
            from document import NFe200
            nfe_obj = NFe200()

        return nfe_obj








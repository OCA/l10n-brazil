# -*- coding: utf-8 -*-
###############################################################################
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
###############################################################################


class NfeFactory(object):

    def get_nfe(self, nfe_version):
        """
        Retorna objeto NFe de acordo com a versao de NFe em uso no OpenERP
        :param company: objeto res.company
        :return: Objeto Nfe
        """
        if nfe_version == '4.00':
            from openerp.addons.l10n_br_account_product.sped.nfe.document \
                import NFe400
            nfe_obj = NFe400()
        elif nfe_version == '3.10':
            from openerp.addons.l10n_br_account_product.sped.nfe.document \
                import NFe310
            nfe_obj = NFe310()
        else:
            from openerp.addons.l10n_br_account_product.sped.nfe.document \
                import NFe200
            nfe_obj = NFe200()
        return nfe_obj

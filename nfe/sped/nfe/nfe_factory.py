# -*- coding: utf-8 -*-
# Copyright (C) 2013  Renato Lima - Akretion
# Copyright (C) 2014 - Michell Stuttgart Faria (<http://www.kmee.com.br>)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html


class NfeFactory(object):

    def get_nfe(self, nfe_version):
        """
        Retorna objeto NFe de acordo com a versao de NFe em uso no OpenERP
        :param company: objeto res.company
        :return: Objeto Nfe
        """
        if nfe_version == '4.00':
            from odoo.addons.l10n_br_account_product.sped.nfe.document \
                import NFe400
            nfe_obj = NFe400()
        elif nfe_version == '3.10':
            from odoo.addons.l10n_br_account_product.sped.nfe.document \
                import NFe310
            nfe_obj = NFe310()
        else:
            from odoo.addons.l10n_br_account_product.sped.nfe.document \
                import NFe200
            nfe_obj = NFe200()
        return nfe_obj

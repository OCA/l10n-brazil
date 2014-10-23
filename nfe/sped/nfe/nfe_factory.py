# -*- coding: utf-8 -*-
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








# -*- coding: utf-8 -*-
# Copyright (C) 2013  Renato Lima - Akretion
# Copyright (C) 2014  Michell Stuttgart Faria - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html


class XMLValidator(object):

    @staticmethod
    def validation(nfe_xml, nfe_obj):

        nfe = nfe_obj.get_NFe()
        nfe.set_xml(nfe_xml)

        return nfe.validar()

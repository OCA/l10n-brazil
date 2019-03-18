# -*- coding: utf-8 -*-
# Copyright (C) 2019 ABGF (http://www.abgf.gov.br)

from openerp import fields, models, api
from openerp.exceptions import Warning as UserError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    def __levenshtein(self, val, field="email", level=3):
        '''
        Verifica verifica se existe correspondência na tabela res_partner
        com base em uma margem de erro.

        :param val: valor a ser buscado
        :param field: campo na tabela res_partner
        :param level: número de divergências possíveis
        :return: True/False
        '''
        request = "CREATE EXTENSION IF NOT EXISTS fuzzystrmatch; " \
                  "SELECT {} FROM res_partner WHERE levenshtein" \
                  "('{}', {}) <= {} ".format(field, val, field, level)

        self.env.cr.execute(request)

        return False if len(self.env.cr.fetchall()) == 0 else True

    @api.model
    def create(self, vals):

        #CONTINUA DAQUI (VALIDAÇÃO SE O USUÁRIO DESSE PARTNER EXITE)
        result_user = self.env['res.users'].search([('login', '=', vals['email'])])

        email_existe = \
            self.__levenshtein(vals.get('email'), field='email', level=3)
        name_existe = \
            self.__levenshtein(vals.get('name'), field='name', level=3)

        # se existir correspondencia do nome + email na tabela res_partner
        # para o processo e impede a inclusão.
        if email_existe and name_existe:
            raise UserError("Parceiro já cadastrado. Por favor, "
                            "verifique na lista ou valide o nome e email.")

        return super(ResPartner, self).create(vals)

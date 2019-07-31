# -*- coding: utf-8 -*-
# Copyright (C) 2019 ABGF (http://www.abgf.gov.br)

from openerp import fields, models, api
from openerp.exceptions import Warning as UserError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # sobreescreve os campos do core retirando o grupo
    signup_token = fields.Char(groups=False)
    signup_type = fields.Char(groups=False)
    signup_expiration = fields.Datetime(groups=False)

    def levenshtein(self, val, tabela='res_partner', field="email", level=3):
        '''
        Verifica verifica se existe correspondência com base em uma
        margem de erro.

        :param val: valor a ser buscado
        :param tabela: tabela
        :param field: campo na tabela
        :param level: número de divergências possíveis
        :return: True/False
        '''
        request = "CREATE EXTENSION IF NOT EXISTS fuzzystrmatch; " \
                  "SELECT {} FROM {} WHERE levenshtein" \
                  "('{}', {}) <= {} ".format(field, tabela, val, field, level)

        self.env.cr.execute(request)

        return False if len(self.env.cr.fetchall()) == 0 else True

    @api.model
    def create(self, vals):
        # verifica e-mail completo na tabela usuário e vinculo com partner
        result_user = False
        if vals.get('email'):
            result_user = self.env['res.users'].search(
                ['|', ('login', '=', vals['email']),
                ('partner_id.email', '=', vals['email'])])

        email_existe = \
            self.levenshtein(vals.get('email'), tabela='res_partner',
                               field='email', level=3)
        name_existe = \
            self.levenshtein(vals.get('name'), field='name', level=3)

        # se existir correspondencia do nome + email na tabela res_partner
        # para o processo e impede a inclusão.
        if email_existe or name_existe or result_user:
            raise UserError("Parceiro já cadastrado. Por favor, "
                            "verifique na lista ou valide o nome e email.")

        return super(ResPartner, self).create(vals)

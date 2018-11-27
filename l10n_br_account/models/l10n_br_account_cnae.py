# -*- coding: utf-8 -*-
# Copyright (C) 2009 - TODAY Renato Lima - Akretion
# Copyright (C) 2014  KMEE - www.kmee.com.br
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields, api


class L10nBrAccountCNAE(models.Model):
    """Classe para cadastro de Código Nacional de Atividade Econômica.

        Os CNAEs são utilizados no cadastro de empresa para definir o
    ramo de atividade primário e secundários das empresas cadastradas no Odoo.
    """
    _name = 'l10n_br_account.cnae'
    _description = 'Cadastro de CNAE'

    code = fields.Char(
        string=u'Código',
        size=16,
        required=True)

    name = fields.Char(
        string=u'Descrição',
        size=64,
        required=True)

    version = fields.Char(
        string=u'Versão',
        size=16,
        required=True)

    parent_id = fields.Many2one(
        comodel_name='l10n_br_account.cnae',
        string=u'CNAE Pai')

    child_ids = fields.One2many(
        comodel_name='l10n_br_account.cnae',
        inverse_name='parent_id',
        string=u'CNAEs Filhos')

    internal_type = fields.Selection(
        [('view', u'Visualização'),
         ('normal', 'Normal')],
        u'Tipo Interno',
        required=True,
        default='normal')

    @api.multi
    def name_get(self):
        return [(r.id,
                u"{0} - {1}".format(r.code, r.name))
                for r in self]

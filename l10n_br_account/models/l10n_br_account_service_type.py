# -*- coding: utf-8 -*-
# Copyright (C) 2009 - TODAY Renato Lima - Akretion
# Copyright (C) 2014  KMEE - www.kmee.com.br
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields, api


class L10nBrAccountServiceType(models.Model):
    _name = 'l10n_br_account.service.type'
    _description = u'Cadastro de Operações Fiscais de Serviço'

    code = fields.Char(
        string=u'Código',
        size=16,
        required=True)

    name = fields.Char(
        string=u'Descrição',
        size=256,
        required=True)

    parent_id = fields.Many2one(
        comodel_name='l10n_br_account.service.type',
        string=u'Tipo de Serviço Pai')

    child_ids = fields.One2many(
        comodel_name='l10n_br_account.service.type',
        inverse_name='parent_id',
        string=u'Tipo de Serviço Filhos')

    internal_type = fields.Selection(
        selection=[('view', u'Visualização'),
                   ('normal', 'Normal')],
        string=u'Tipo Interno',
        required=True,
        default='normal')

    @api.multi
    def name_get(self):
        return [(r.id,
                u"{0} - {1}".format(r.code, r.name))
                for r in self]

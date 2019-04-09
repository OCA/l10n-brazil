# -*- coding: utf-8 -*-
# Copyright 2019 ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import fields, models


class AccountDeParaPlano(models.Model):
    _name = 'account.depara.plano'
    _description = u'Referência dos Planos de Contas Externos'

    name = fields.Char(
        string='Plano de Contas',
    )

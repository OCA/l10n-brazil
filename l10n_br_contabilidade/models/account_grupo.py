# -*- coding: utf-8 -*-
# Copyright 2018 ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models
from openerp.exceptions import Warning


class AccountGrupoRamo(models.Model):
    _name = 'account.grupo'
    _description = 'Grupo dos ramos de seguros para fins de contabilização'
    _order = 'name'

    name = fields.Char(
        string=u'Nome',
        required=True,
    )

    account_ramo_ids = fields.One2many(
        comodel_name='account.ramo',
        inverse_name='grupo_id',
        string=u'Grupos',
    )

    code = fields.Char(
        string=u'Código',
        size=2,
        required=True,
    )

    descricao = fields.Char(
        string=u'Descrição',
    )

    @api.one
    def name_get(self):
        name = self.code+" - "+self.name
        return (self.id, name)

    @api.onchange('code')
    def _on_change_code(self):
        try:
            int(self.code)
            pass
        except ValueError:
            raise Warning(u'O campo "Código" deve conter dois dígitos e apenas números.')
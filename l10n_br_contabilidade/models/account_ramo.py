# -*- coding: utf-8 -*-
# Copyright 2018 ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models
from openerp.exceptions import except_orm, Warning, RedirectWarning

class AccountRamo(models.Model):
    _name = 'account.ramo'
    _description = 'Ramos de seguros para fins de contabilização'
    _order = 'name'

    name = fields.Char(
        string=u'Nome',
        required=True,
    )

    grupo_id = fields.Many2one(
        comodel_name='account.grupo',
        string=u'Grupo',
        required=True,
    )

    identificador = fields.Char(
        string=u'Identificador',
        size=2,
        required=True,
    )

    code = fields.Char(
        string=u'Código',
        compute='compute_code_grupo_ramo',
        store=True,
        help=u'Para fins de armazenamento de dados, o código do ramo de seguro é composto '
             u'pelos campos "Código Grupo" e "Identificador do Ramo", totalizando quatro dígitos.',
    )

    observacao = fields.Text(
        string=u'Observação',
    )

    @api.depends('grupo_id','identificador')
    def compute_code_grupo_ramo(self):
        for record in self:
            record.code = record.grupo_id.code+record.identificador

    @api.onchange('identificador')
    def _on_change_identificador(self):
        try:
            int(self.identificador)
            pass
        except ValueError:
            raise Warning(u'O campo "identificador" deve conter apenas números.')

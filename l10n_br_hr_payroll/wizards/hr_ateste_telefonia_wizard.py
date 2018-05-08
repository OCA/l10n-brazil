# -*- coding: utf-8 -*-
# Copyright 2018 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, models, fields
from openerp.exceptions import ValidationError


class HrTelefoniaWizard(models.TransientModel):
    _name = 'hr.ateste.telefonia.wizard'

    mensagem_ateste = fields.Char(
        string='Mensagem do Ateste',
        readonly=True,
        default=u'Atesto que as ligações previamente selecionadas foram particulares.',
    )

    ligacoes_ids = fields.Many2many(
        comodel_name='hr.telefonia.line',
        string=u'Ligacoes',
        relation='ateste_ligacoes_wizard_rel',
        column1='wizard_id',
        column2='ligacoes_id',
    )

    @api.multi
    def atestar_ligacoes_particulares(self):
        '''
        Setar ligacoes do wizard como particulares
        :return:
        '''
        proxy = self.env['hr.telefonia.line']

        for record in proxy.browse(self._context.get('active_ids', [])):
            if not record.employee_id or not record.ramal:
                raise ValidationError('Faltando informações na ligação!')
            record.set_validate_ligacoes()
        return {'type': 'ir.actions.act_window_close'}

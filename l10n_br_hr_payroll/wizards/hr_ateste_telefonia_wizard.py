# -*- coding: utf-8 -*-
# Copyright 2018 ABGF BR
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, models, fields
from openerp.exceptions import ValidationError


class HrTelefoniaWizard(models.TransientModel):
    _name = 'hr.ateste.telefonia.wizard'

    mensagem_ateste = fields.Char(
        string='Mensagem do Ateste',
        readonly=True,
        default=u'Atesto as ligações previamente selecionadas.',
    )

    mensagem_valor = fields.Char(
        string='Mensagem do Valor total',
        readonly=True,
        default=u'Total das ligações particulares: R$ 0.00',
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

    @api.model
    def default_get(self, fields):
        """
        Setar valor total das ligações selecionadas para ateste
        :param fields:
        :return:
        """
        res = super(HrTelefoniaWizard, self).default_get(fields)

        hr_telefonia_line_ids = \
            self.env['hr.telefonia.line'].browse(self.env.context.get('active_ids'))

        total = sum(hr_telefonia_line_ids.filtered(
            lambda x: x.tipo == 'particular').mapped('valor'))

        mensagem  = 'Total das ligações particulares: R$ ' + \
                    (str(total)).replace('.', ',') + ' .'

        res.update({
            'mensagem_valor': mensagem,
            # 'ligacoes_ids': (6, 0, hr_telefonia_line_ids.ids),
        })
        return res

# -*- coding: utf-8 -*-
# Copyright 2017 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models
from openerp.exceptions import ValidationError


class HrContract(models.Model):

    _inherit = 'hr.contract'

    # Registro S-2200
    sped_S2200 = fields.Boolean(
        string='Cadastro do Vínculo',
        compute='_compute_sped_S2200',
    )
    sped_S2200_registro = fields.Many2one(
        string='Registro S-2200 - Cadastramento Inicial do Vínculo',
        comodel_name='sped.transmissao',
    )
    sped_S2200_situacao = fields.Selection(
        string='Situação S-2200',
        selection=[
            ('1', 'Pendente'),
            ('2', 'Transmitida'),
            ('3', 'Erro(s)'),
            ('4', 'Sucesso'),
        ],
        related='sped_S2200_registro.situacao',
        readonly=True,
    )
    sped_S2200_data_hora = fields.Datetime(
        string='Data/Hora',
        related='sped_S2200_registro.data_hora_origem',
        readonly=True,
    )

    @api.depends('sped_S2200_registro')
    def _compute_sped_S2200(self):
        for contrato in self:
            contrato.sped_S2200 = True if contrato.sped_S2200_registro else False

    @api.multi
    def criar_S2200(self):
        self.ensure_one()
        if self.sped_S2200_registro:
            raise ValidationError('Esta contrato já registro este vínculo')

        values = {
            'tipo': 'esocial',
            'registro': 'S-2200',
            'ambiente': self.company_id.esocial_tpAmb or self.company_id.matriz.esocial_tpAmb,
            'company_id': self.company_id.id,
            'evento': 'evtAdmissao',
            'origem': ('hr.contract,%s' % self.id),
        }

        sped_S2200_registro = self.env['sped.transmissao'].create(values)
        self.sped_S2200_registro = sped_S2200_registro

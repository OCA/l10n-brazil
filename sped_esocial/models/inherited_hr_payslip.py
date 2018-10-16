# -*- coding: utf-8 -*-
# Copyright 2018 ABGF - http://www.abgf.gov.br
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, models, fields


class HrPaylisp(models.Model):
    _inherit = "hr.payslip"

    # Campo motificado para utilizar a tabela de campos do e-Social
    # Tabela 19 - Motivos de Desligamento
    mtv_deslig_esocial = fields.Many2one(
        string='Motivo Desligamento',
        comodel_name='sped.motivo_desligamento',
        help="e-Social: S-2299 - mtvDeslig"
    )

    sped_s2299 = fields.Many2one(
        string='Registro SPED S-2299',
        comodel_name='sped.hr.rescisao',
    )
    situacao_esocial_s2299 = fields.Selection(
        selection=[
            ('0', 'Inativo'),
            ('1', 'Ativo'),
            ('2', 'Precisa Atualizar'),
            ('3', 'Aguardando Transmissão'),
            ('4', 'Aguardando Processamento'),
            ('5', 'Erro(s)'),
            ('9', 'Finalizado'),
        ],
        string='Situação no e-Social',
        related='sped_s2299.situacao_s2299',
        readonly=True,
    )

    # sped_s2399 = fields.Many2one(
    #     string='Registro SPED S-2399',
    #     comodel_name='sped.hr.rescisao.autonomo',
    # )

    @api.multi
    def hr_verify_sheet(self):
        for holerite in self:
            if holerite.state == 'draft':
                if holerite.tipo_de_folha == 'rescisao':
                    holerite.contract_id.resignation_cause_id = \
                        holerite.mtv_deslig_esocial
                    holerite.contract_id.resignation_date = \
                        holerite.data_afastamento
            super(HrPaylisp, holerite).hr_verify_sheet()

    @api.model
    def create(self, vals):
        if vals.get('mtv_deslig_esocial'):
            vals['mtv_deslig'] = self.retorna_motivo_desligamento(vals['mtv_deslig_esocial'])

        return super(HrPaylisp, self).create(vals)

    @api.multi
    def write(self, vals):
        for record in self:
            if vals.get('mtv_deslig_esocial'):
                vals['mtv_deslig'] = record.retorna_motivo_desligamento(vals['mtv_deslig_esocial'])
            super(HrPaylisp, record).write(vals)

        return True

    def retorna_motivo_desligamento(self, motivo_id):
        """
        Função responsável por retornor o código e a descrição do motivo de desligamento por extenso através do
        id do motivo.
        """
        mtv_desligamento_esocial = self.env['sped.motivo_desligamento'].browse(motivo_id)

        return '{}-{}'.format(mtv_desligamento_esocial.codigo, mtv_desligamento_esocial.nome)

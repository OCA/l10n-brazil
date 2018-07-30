# -*- coding: utf-8 -*-
# Copyright 2017 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models
from openerp.exceptions import ValidationError


class HrContractChange(models.Model):

    _inherit = 'l10n_br_hr.contract.change'

    # Relacionamentos com os diversos registros intermediários possível
    #
    # S-2206 (Alteração Contratual)
    sped_s2206_id = fields.Many2one(
        string='SPED Alteração Contratual (S-2206)',
        comodel_name='sped.esocial.alteracao.contrato',
    )
    #
    # Registros que calculam situação do contrato no e-Social
    situacao_esocial = fields.Selection(
        selection=[
            ('0', 'Inativo'),
            ('1', 'Ativo'),
            ('2', 'Precisa Atualizar'),
            ('3', 'Aguardando Transmissão'),
            ('4', 'Aguardando Processamento'),
            ('5', 'Erro(s)'),
            ('8', 'Provisório'),
            ('9', 'Finalizado'),
        ],
        string='Situação no e-Social',
        compute='compute_situacao_esocial',
        # store=True,
    )
    precisa_atualizar = fields.Boolean(
        string='Precisa Atualizar',
    )

    # Método que calcula a situação do contrato no e-Social
    @api.depends('sped_s2206_id')
    def compute_situacao_esocial(self):
        for change in self:
            situacao_esocial = '0'  # Inativo

            # Se tiver um registro S-2206
            # transmitido com sucesso então é Ativo
            if change.sped_s2206_id:
                if change.sped_s2206_id.situacao_esocial == '4':
                    situacao_esocial = '1'  # Ativo

            # Se precisa_atualizar ou retificar então é Precisa Atualizar
            if change.precisa_atualizar:
                situacao_esocial = '2'  # Precisa Atualizar

            # Se tem algum registro aguardando transmissão então é Aguardando Transmissão
            if change.sped_s2206_id:
                if change.sped_s2206_id.situacao_esocial == '1':
                    situacao_esocial = '3'

            # Se tiver algum registro já transmitido então é Aguardando Processamento
            # if contrato.sped_s2190_id.situacao_esocial == '2':   # Quando implementarmos o S-2190
            #     situacao_esocial = '4'
            if change.sped_s2206_id:
                if change.sped_s2206_id.situacao_esocial == '2':
                    situacao_esocial = '4'

            # Se tiver algum registro com erro então é Erro(s)
            # if contrato.sped_s2190_id.situacao_esocial == '3':   # Quando implementarmos o S-2190
            #     situacao_esocial = '5'
            if change.sped_s2206_id:
                if change.sped_s2206_id.situacao_esocial == '3':
                    situacao_esocial = '5'

            # Popula na tabela
            change.situacao_esocial = situacao_esocial

    @api.multi
    def write(self, vals):
        self.ensure_one()

        # Lista os campos que são monitorados da Alteração Contratual
        campos_monitorados = [
            # TODO Inserir os campos a serem monitorados no contrato
            'vinculo',                       # //eSocial/evtAdmissao/vinculo/matricula
        ]
        precisa_atualizar = False

        # Roda o vals procurando se algum desses campos está na lista
        if self.situacao_esocial == '1':
            for campo in campos_monitorados:
                if campo in vals:
                    precisa_atualizar = True

            # Se precisa_atualizar == True, inclui ele no vals
            if precisa_atualizar:
                vals['precisa_atualizar'] = precisa_atualizar

        # Grava os dados
        return super(HrContractChange, self).write(vals)

    @api.multi
    def atualizar_contrato_s2206(self):
        self.ensure_one()

        # Se o registro intermediário do S-2206 não existe, criá-lo
        if not self.sped_s2206_id:
            if self.env.user.company_id.eh_empresa_base:
                matriz = self.env.user.company_id.id
            else:
                matriz = self.env.user.company_id.matriz.id

            self.sped_s2206_id = \
                self.env['sped.esocial.alteracao.contrato'].create({
                    'company_id': matriz,
                    'hr_contract_change_id': self.id,
                })

        # Criar o registro de transmissão relacionado
        self.sped_s2206_id.gerar_registro()

    @api.multi
    def retificar_contrato_s2206(self):  # TODO
        self.ensure_one()

        # Roda o mesmo método de criação (deixe que o registro intermediário lide com a situação)
        self.atualizar_contrato_s2206()

    @api.multi
    def transmitir(self):  # TODO
        self.ensure_one()

        # Se o registro S-2206 estiver pendente transmissão
        if self.sped_s2206_id and self.sped_s2206_id.situacao_esocial in ['1', '3']:
            self.sped_s2206_id.transmitir()
            return

    @api.multi
    def consultar(self):  # TODO
        self.ensure_one()

        # Se o registro S-2206 estiver transmitida
        if self.sped_s2206_id and self.sped_s2206_id.situacao_esocial in ['2']:
            self.sped_s2206_id.consultar()
            return

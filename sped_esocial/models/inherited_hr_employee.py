# -*- coding: utf-8 -*-
# Copyright 2018 ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, models, fields


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    # Campos de controle do e-Social
    # S-2205 (Alteração de Dados Cadastrais do Trabalhador)
    sped_s2205_ids = fields.Many2many(
        string='SPED Alterações Dados Cadastrais (S-2205)',
        comodel_name='sped.esocial.alteracao.funcionario',
    )
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
    )
    precisa_atualizar = fields.Boolean(
        string='Precisa Atualizar',
    )

    # Calcula a situação e-Social levando em conta a situação do contrato também.
    @api.depends('contract_ids')
    def compute_situacao_esocial(self):
        for trabalhador in self:

            # Identifica o primeiro contrato ativo
            contrato_valido = False
            for contrato in trabalhador.contract_ids:
                if contrato.situacao_esocial not in ['9']:
                    contrato_valido = contrato
            if not contrato_valido:  # Se todos os contratos já estão finalizado, pega o primeiro mesmo
                if trabalhador.contract_ids:
                    contrato_valido = trabalhador.contract_ids[0]

            situacao_esocial = '0'  # Inativo

            # Se tem um contrato_valido, roda o código abaixo
            if contrato_valido:
                # Dependendo da situação do contrato, identifica qual é a situação do funcionário
                if contrato_valido.situacao_esocial in ['1', '2', '3', '4', '5', '8']:
                    if contrato_valido.situacao_esocial in ['1', '2', '8']:
                        situacao_esocial = '1'  # Ativo
                    if contrato_valido.situacao_esocial in ['3', '4', '5']:
                        situacao_esocial = '2'

                    # Se precisa_atualizar o funcionário, verifique a situação da transmissão
                    if trabalhador.precisa_atualizar:
                        situacao_esocial = '2'  # Precisa Atualizar

                        # Se já existe um registro de alteração aberto,
                        # muda a situação dependendo da situação do registro
                        for s2205 in trabalhador.sped_s2205_ids:
                            if s2205.situacao_esocial in ['1']:  # Precisa Transmitir
                                situacao_esocial = '3'
                                continue
                            if s2205.situacao_esocial in ['2']:  # Transmitida
                                situacao_esocial = '4'
                                continue
                            if s2205.situacao_esocial in ['3']:  # Erro(s)
                                situacao_esocial = '5'
                                continue

                elif contrato_valido.situacao_esocial in ['9']:
                    situacao_esocial = '9'

            # Popula o campo na tabela
            trabalhador.situacao_esocial = situacao_esocial

    @api.multi
    def write(self, vals):
        self.ensure_one()

        # Lista os campos que são monitorados do Empregador
        campos_monitorados = [
            # TODO Inserir os campos a serem monitorados no trabalhador
            'cnpj_cpf',  # //eSocial/evtInfoEmpregador/ideEmpregador/nrInsc
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
        return super(HrEmployee, self).write(vals)

    # Cria campos pais_nac_id e pais_nascto_id para substituir o place_of_birth (que é texto)
    pais_nascto_id = fields.Many2one(
        string='País de Nascimento',
        comodel_name='sped.pais',
    )
    pais_nac_id = fields.Many2one(
        string='Nacionalidade',
        comodel_name='sped.pais',
    )

    # Dados que faltam em l10n_br_hr
    cnh_dt_exped = fields.Date(
        string='Data de Emissão',
    )
    cnh_uf = fields.Many2one(
        string='UF',
        comodel_name='res.country.state',
    )
    cnh_dt_pri_hab = fields.Date(
        string='Data da 1ª Hab.',
    )
    sped_esocial_alterar_cadastro_id = fields.Many2one(
        string='Alterar Cadastro',
        comodel_name='sped.esocial.alteracao.funcionario',
    )
    # situacao_esocial_inicial = fields.Selection(
    #     selection=[
    #         ('0', 'Inativa'),
    #         ('1', 'Ativa'),
    #         ('2', 'Precisa Atualizar'),
    #         ('3', 'Aguardando Transmissão'),
    #         ('9', 'Finalizada'),
    #     ],
    #     string='Situação no e-Social',
    #     related='contract_id.situacao_esocial',
    #     readonly=True,
    # )
    # precisa_atualizar = fields.Boolean(
    #     string='Precisa atualizar dados?',
    #     related='sped_esocial_alterar_cadastro_id.precisa_atualizar',
    # )

    @api.multi
    def write(self, vals):
        self._gerar_tabela_intermediaria_alteracao(vals)
        return super(HrEmployee, self).write(vals)

    @api.multi
    def _gerar_tabela_intermediaria_alteracao(self, vals={}):
        # Se o registro intermediário do S-2205 não existe, criá-lo
        if not self.sped_esocial_alterar_cadastro_id and not \
                vals.get('sped_esocial_alterar_cadastro_id'):
            matriz = self.company_id.id if self.company_id.eh_empresa_base \
                else self.company_id.matriz.id
            self.sped_esocial_alterar_cadastro_id = \
                self.env['sped.esocial.alteracao.funcionario'].create(
                    {
                        'company_id': matriz,
                        'hr_employee_id': self.id,
                    }
                )

    @api.multi
    def atualizar_cadastro_funcionario(self):
        self.ensure_one()

        self._gerar_tabela_intermediaria_alteracao()

        # Processa cada tipo de operação do S-2205
        # O que realmente precisará ser feito é
        # tratado no método do registro intermediário
        self.sped_esocial_alterar_cadastro_id.gerar_registro()

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
        store=True,
    )
    precisa_atualizar = fields.Boolean(
        string='Precisa Atualizar',
    )

    # Calcula a situação e-Social levando em conta a situação do contrato também.
    @api.depends('contract_ids', 'sped_s2205_ids')
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
            'marital',                  # //eSocial/evtAltCadastral/ideEmpregador/dadosTrabalhador/estCiv
            'educational_attainment',   # //eSocial/evtAltCadastral/ideEmpregador/dadosTrabalhador/grauInstr
            'ctps',                     # //eSocial/evtAltCadastral/ideEmpregador/dadosTrabalhador/documentos/CTPS/nrCtps
            'ctps_series',              # //eSocial/evtAltCadastral/ideEmpregador/dadosTrabalhador/documentos/CTPS/serieCtps
            'ctps_uf_id',               # //eSocial/evtAltCadastral/ideEmpregador/dadosTrabalhador/documentos/CTPS/ufCtps
            'rg',                       # //eSocial/evtAltCadastral/ideEmpregador/dadosTrabalhador/documentos/RG/nrRG
            'organ_exp',                # //eSocial/evtAltCadastral/ideEmpregador/dadosTrabalhador/documentos/RG/orgaoEmissor
            'rg_emission',              # //eSocial/evtAltCadastral/ideEmpregador/dadosTrabalhador/documentos/RG/dtExped
            'driver_license',           # //eSocial/evtAltCadastral/ideEmpregador/dadosTrabalhador/documentos/CNH/nrRegCnh
            'cnh_dt_exped',             # //eSocial/evtAltCadastral/ideEmpregador/dadosTrabalhador/documentos/CNH/dtExped
            'cnh_uf',                   # //eSocial/evtAltCadastral/ideEmpregador/dadosTrabalhador/documentos/CNH/ufCnh
            'expiration_date',          # //eSocial/evtAltCadastral/ideEmpregador/dadosTrabalhador/documentos/CNH/dtValid
            'cnh_dt_pri_hab',           # //eSocial/evtAltCadastral/ideEmpregador/dadosTrabalhador/documentos/CNH/dtPriHab
            'driver_categ',             # //eSocial/evtAltCadastral/ideEmpregador/dadosTrabalhador/documentos/CNH/categoriaCnh
            'dependent_ids',            # //eSocial/evtAltCadastral/ideEmpregador/dadosTrabalhador/dependente
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

    @api.multi
    def atualizar_trabalhador_s2205(self):  # TODO
        self.ensure_one()

        # Identifica se já existe um registro de atualização em aberto
        sped_s2205 = False
        for s2205 in self.sped_s2205_ids:
            if s2205.situacao_esocial != '4':
                sped_s2205 = s2205

        # Se o registro intermediário do S-2205 não existe, criá-lo
        if not sped_s2205:
            if self.env.user.company_id.eh_empresa_base:
                matriz = self.env.user.company_id.id
            else:
                matriz = self.env.user.company_id.matriz.id

            sped_s2205 = \
                self.env['sped.esocial.alteracao.funcionario'].create({
                    'company_id': matriz,
                    'hr_employee_id': self.id,
                })
            self.sped_s2205_ids = [(4, sped_s2205.id)]

        # Criar o registro de transmissão relacionado
        sped_s2205.gerar_registro()

    @api.multi
    def transmitir(self):  # TODO
        self.ensure_one()

        # Se algum registro S-2205 estiver pendente transmissão
        for s2205 in self.sped_s2205_ids:
            if s2205.situacao_esocial in ['1', '3']:
                s2205.transmitir()
                return

    @api.multi
    def consultar(self):  # TODO
        self.ensure_one()

        # Se algum registro S-2205 estiver transmitida
        for s2205 in self.sped_s2205_ids:
            if s2205.situacao_esocial in ['2']:
                s2205.consultar()
                return

    @api.multi
    def retorna_trabalhador(self):
        self.ensure_one()

        return self

    # Campos de Trabalhador Extrangeiro
    dt_chegada = fields.Date(
        string='Data de chegada no Brasil',
    )
    class_trab_estrang = fields.Selection(
        string='Condição do Extrangeiro no Brasil',
        selection=[
            ('1',  '1-Visto Permanente'),
            ('2',  '2-Visto temporário'),
            ('3',  '3-Asilado'),
            ('4',  '4-Refugiado'),
            ('5',  '5-Solicitante de Refúgio'),
            ('6',  '6-Residente fora do Brasil'),
            ('7',  '7-Deficiente físico e com mais de 51 anos'),
            ('8',  '8-Com residência provisória e anistiado, em situação irregular'),
            ('9',  '9-Permanência no Brasil em razão de filhos ou cônjuge brasileiros'),
            ('10', '10-Beneficiado pelo acordo entre países do Mercosul'),
            ('11', '11-Dependente de agente diplomático e/ou consular de países que mantém convênio de reciprocidade para o exercício de atividade remunerada no Brasil'),
            ('12', '12-Beneficiado pelo Tratado de Amizade, Cooperação e Consulta entre a República Federativa do Brasil e a República Portuguesa'),
        ],
    )
    casado_br = fields.Selection(
        string='Casado(a) com Brasileiro(a)',
        selection=[
            ('S', 'S-Sim'),
            ('N', 'N-Não'),
        ],
    )
    filhos_br = fields.Selection(
        string='Tem filhos brasileiros',
        selection=[
            ('S', 'S-Sim'),
            ('N', 'N-Não'),
        ],
    )

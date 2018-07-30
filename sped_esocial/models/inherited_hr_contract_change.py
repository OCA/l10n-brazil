# -*- coding: utf-8 -*-
# Copyright 2017 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models
from openerp.exceptions import ValidationError


class HrContract(models.Model):

    _inherit = 'hr.contract'

    # Relacionamentos com os diversos registros intermediários possível
    #
    # S-2190 (Admissão do Trabalhador - Registro Preliminar)
    # sped_s2190_id = fields.Many2one(   # Quando implementarmos o S-2190
    #     string='SPED Contrato S-2190',
    #     comodel_name='sped.esocial.contrato_preliminar',
    # )
    #
    # S-2200 (Admissão do Trabalhador) - Inicial
    sped_s2200_id = fields.Many2one(
        string='SPED Contrato (S-2200)',
        comodel_name='sped.esocial.contrato',
    )
    #
    # S-2206 (Alteração Contratual)
    sped_s2206_ids = fields.Many2many(
        string='SPED Alterações Contratuais (S-2206)',
        comodel_name='sped.esocial.alteracao.contrato',
    )
    #
    # S-2299 (Desligamentos)
    sped_s2299_ids = fields.Many2many(
        string='SPED Desligamentos (S-2299)',
        comodel_name='sped.hr.rescisao',
    )
    # # S-2298 (Reintegrações)
    # sped_s2298_ids = fields.Many2many(   # Quando implementarmos o S-2298
    #     string='SPED Reintegrações S-2298',
    #     comodel_name='sped.hr.reintegracao',
    # )
    #
    # S-2300 (Trabalhador sem Vínculo - Início)
    sped_s2300_id = fields.Many2one(
        string='SPED Trabalhador sem Vínculo - Início (S-2300)',
        comodel_name='sped.esocial.contrato.autonomo',
    )
    # S-2306 (Trabalhador sem Vínculo - Alteração)
    sped_s2306_ids = fields.Many2many(
        string='SPED Trabalhador sem Vínculo - Alteração (S-2306)',
        comodel_name='sped.esocial.alteracao.contrato.autonomo',
    )
    #
    # S-2399 (Trabalhador sem Vínculo - Término)
    sped_s2399_id = fields.Many2one(
        string='SPED Trabalhador sem Vínculo - Término (S-2399)',
        comodel_name='sped.hr.rescisao.autonomo',
    )

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
    @api.depends('sped_s2200_id', 'sped_s2206_ids', 'sped_s2299_ids', 'sped_s2300_id', 'sped_s2306_ids', 'sped_s2399_id')
    def compute_situacao_esocial(self):
        for contrato in self:
            situacao_esocial = '0'  # Inativo

            # # Se tiver um registro S-2190 transmitido com sucesso então é Provisório
            # if contrato.sped_s2190_id.situacao_esocial == '4':   # Quando implementarmos o S-2190
            #     situacao_esocial = '8'  # Provisório

            # Se tiver um registro S-2200 ou um S-2300
            # transmitido com sucesso então é Ativo
            if contrato.sped_s2200_id:
                if contrato.sped_s2200_id.situacao_esocial == '4':
                    situacao_esocial = '1'  # Ativo
            if contrato.sped_s2300_id:
                if contrato.sped_s2300_id.situacao_esocial == '4':
                    situacao_esocial = '1'  # Ativo

            # Se precisa_atualizar ou retificar então é Precisa Atualizar
            if contrato.precisa_atualizar:
                situacao_esocial = '2'  # Precisa Atualizar

            # Se tem algum registro aguardando transmissão então é Aguardando Transmissão
            # if contrato.sped_s2190_id.situacao_esocial == '1':   # Quando implementarmos o S-2190
            #     situacao_esocial = '3'
            if contrato.sped_s2200_id:
                if contrato.sped_s2200_id.situacao_esocial == '1':
                    situacao_esocial = '3'
            if contrato.sped_s2300_id:
                if contrato.sped_s2300_id.situacao_esocial == '1':
                    situacao_esocial = '3'
            for s2206 in contrato.sped_s2206_ids:
                if s2206.situacao_esocial == '1':
                    situacao_esocial = '3'
            for s2299 in contrato.sped_s2299_ids:
                if s2299.situacao_esocial == '1':
                    situacao_esocial = '3'
            # for s2298 in contrato.sped_s2298_ids:   # Quando implementarmos o S-2298
            #     if s2298.situacao_esocial == '1':
            #         situacao_esocial = '3'
            for s2306 in contrato.sped_s2306_ids:
                if s2306.situacao_esocial == '1':
                    situacao_esocial = '3'
            if contrato.sped_s2399_id:
                if contrato.sped_s2399_id.situacao_esocial == '1':
                    situacao_esocial = '3'

            # Se tiver algum registro já transmitido então é Aguardando Processamento
            # if contrato.sped_s2190_id.situacao_esocial == '2':   # Quando implementarmos o S-2190
            #     situacao_esocial = '4'
            if contrato.sped_s2200_id:
                if contrato.sped_s2200_id.situacao_esocial == '2':
                    situacao_esocial = '4'
            if contrato.sped_s2300_id:
                if contrato.sped_s2300_id.situacao_esocial == '2':
                    situacao_esocial = '4'
            for s2206 in contrato.sped_s2206_ids:
                if s2206.situacao_esocial == '2':
                    situacao_esocial = '4'
            for s2299 in contrato.sped_s2299_ids:
                if s2299.situacao_esocial == '2':
                    situacao_esocial = '4'
            # for s2298 in contrato.sped_s2298_ids:   # Quando implementarmos o S-2298
            #     if s2298.situacao_esocial == '2':
            #         situacao_esocial = '4'
            for s2306 in contrato.sped_s2306_ids:
                if s2306.situacao_esocial == '2':
                    situacao_esocial = '4'
            if contrato.sped_s2399_id:
                if contrato.sped_s2399_id.situacao_esocial == '2':
                    situacao_esocial = '4'

            # Se tiver algum registro com erro então é Erro(s)
            # if contrato.sped_s2190_id.situacao_esocial == '3':   # Quando implementarmos o S-2190
            #     situacao_esocial = '5'
            if contrato.sped_s2200_id:
                if contrato.sped_s2200_id.situacao_esocial == '3':
                    situacao_esocial = '5'
            if contrato.sped_s2300_id:
                if contrato.sped_s2300_id.situacao_esocial == '3':
                    situacao_esocial = '5'
            for s2206 in contrato.sped_s2206_ids:
                if s2206.situacao_esocial == '3':
                    situacao_esocial = '5'
            for s2299 in contrato.sped_s2299_ids:
                if s2299.situacao_esocial == '3':
                    situacao_esocial = '5'
            # for s2298 in contrato.sped_s2298_ids:   # Quanto implementarmos o S-2298
            #     if s2298.situacao_esocial == '3':
            #         situacao_esocial = '5'
            for s2306 in contrato.sped_s2306_ids:
                if s2306.situacao_esocial == '3':
                    situacao_esocial = '5'
            if contrato.sped_s2399_id:
                if contrato.sped_s2399_id.situacao_esocial == '3':
                    situacao_esocial = '5'

            # Se tiver algum registro S-2299 com sucesso então é Finalizado
            for s2299 in contrato.sped_s2299_ids:
                if s2299.situacao_esocial == '4':
                    situacao_esocial = '9'

            # Se tiver registro S-2399 com sucesso então é Finalizado
            if contrato.sped_s2399_id:
                if contrato.sped_s2399_id.situacao_esocial == '4':
                    situacao_esocial = '9'

            # TODO Calcular se o contrato foi reativado devido a algum registro S-2298, e se tiver tem que levar em
            # conta qual é o último registro pela data de transmissão, o S-2298 ou o S-2299
            # Se o último for S-2299, então o contrato está finalizado mesmo
            # Se o último for S-2298, então o contrato está Ativo

            # Popula na tabela
            contrato.situacao_esocial = situacao_esocial

    @api.multi
    def write(self, vals):
        self.ensure_one()

        # Lista os campos que são monitorados do Empregador
        campos_monitorados = [
            # TODO Inserir os campos a serem monitorados no contrato
            'vinculo',                       # //eSocial/evtAdmissao/vinculo/matricula
            'labor_regime_id',               # //eSocial/evtAdmissao/vinculo/tpRegTrab
            'tp_reg_prev',                   # //eSocial/evtAdmissao/vinculo/tpRegPrev
            'cad_ini',                       # //eSocial/evtAdmissao/vinculo/cadIni
            'date_start',                    # //eSocial/evtAdmissao/vinculo/infoRegimeTrab/infoCeletista/dtAdm
                                             # //eSocial/evtAdmissao/vinculo/infoRegimeTrab/infoEstatutario/dtNomeacao
            'admission_type_id',             # //eSocial/evtAdmissao/vinculo/infoRegimeTrab/infoCeletista/tpAdmissao
            'indicativo_de_admissao',        # //eSocial/evtAdmissao/vinculo/infoRegimeTrab/infoCeletista/indAdmissao
            'tp_reg_jor',                    # //eSocial/evtAdmissao/vinculo/infoRegimeTrab/infoCeletista/tpRegJor
            'nat_atividade',                 # //eSocial/evtAdmissao/vinculo/infoRegimeTrab/infoCeletista/natAtividade
            'partner_union',                 # //eSocial/evtAdmissao/vinculo/infoRegimeTrab/infoCeletista/cnpjSindCategProf
            'opc_fgts',                      # //eSocial/evtAdmissao/vinculo/infoRegimeTrab/infoCeletista/FGTS/opcFGTS
            'dt_opc_fgts',                   # //eSocial/evtAdmissao/vinculo/infoRegimeTrab/infoCeletista/FGTS/dtOpcFGTS
            'job_id',                        # //eSocial/evtAdmissao/vinculo/infoContrato/codCargo
            'categoria',                     # //eSocial/evtAdmissao/vinculo/infoContrato/codCateg
            'wage',                          # //eSocial/evtAdmissao/vinculo/infoContrato/remuneracao/vrSalFx
            'salary_unit',                   # //eSocial/evtAdmissao/vinculo/infoContrato/remuneracao/undSalFixo
            'dsc_sal_var',                   # //eSocial/evtAdmissao/vinculo/infoContrato/remuneracao/dscSalVar
            'tp_contr',                      # //eSocial/evtAdmissao/vinculo/infoContrato/duracao/tpContr
            'date_end',                      # //eSocial/evtAdmissao/vinculo/infoContrato/duracao/dtTerm
            'clau_assec',                    # //eSocial/evtAdmissao/vinculo/infoContrato/duracao/clauAssec
            'company_id',                    # //eSocial/evtAdmissao/vinculo/infoContrato/localTrabalho/localTrabGeral/nrInsc
            'weekly_hours',                  # //eSocial/evtAdmissao/vinculo/infoContrato/horContratual/qtdHrsSem
            'tp_jornada',                    # //eSocial/evtAdmissao/vinculo/infoContrato/horContratual/tpJornada
            'dsc_tp_jorn',                   # //eSocial/evtAdmissao/vinculo/infoContrato/horContratual/dscTpJorn
            'tmp_parc',                      # //eSocial/evtAdmissao/vinculo/infoContrato/horContratual/tmpParc
            'working_hours',                 # //eSocial/evtAdmissao/vinculo/infoContrato/horContratual/horario **
            'notes',                         # //eSocial/evtAdmissao/vinculo/infoContrato/observacoes/observacao
            'cnpj_empregador_anterior',      # //eSocial/evtAdmissao/vinculo/sucessaoVinc/cnpjEmpregAnt
            'matricula_anterior',            # //eSocial/evtAdmissao/vinculo/sucessaoVinc/matricAnt
            'observacoes_vinculo_anterior',  # //eSocial/evtAdmissao/vinculo/sucessaoVinc/observacao
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
        return super(HrContract, self).write(vals)

    @api.multi
    def ativar_contrato_s2200(self):  # TODO
        self.ensure_one()

        # Se o registro intermediário do S-2200 não existe, criá-lo
        if not self.sped_s2200_id:
            if self.env.user.company_id.eh_empresa_base:
                matriz = self.env.user.company_id.id
            else:
                matriz = self.env.user.company_id.matriz.id

            self.sped_s2200_id = \
                self.env['sped.esocial.contrato'].create({
                    'company_id': matriz,
                    'hr_contract_id': self.id,
                })

        # Criar o registro de transmissão relacionado
        self.sped_s2200_id.gerar_registro()

    @api.multi
    def ativar_contrato_s2300(self):  # TODO
        self.ensure_one()

        # Se o registro intermediário do S-2200 não existe, criá-lo
        if not self.sped_s2300_id:
            if self.env.user.company_id.eh_empresa_base:
                matriz = self.env.user.company_id.id
            else:
                matriz = self.env.user.company_id.matriz.id

            self.sped_s2300_id = \
                self.env['sped.esocial.contrato.autonomo'].create({
                    'company_id': matriz,
                    'hr_contract_id': self.id,
                })

        # Criar o registro de transmissão relacionado
        self.sped_s2300_id.gerar_registro()

    @api.multi
    def retificar_contrato_s2200(self):  # TODO
        self.ensure_one()

        # Valida se pode ser retificado
        if not self.sped_s2200_id:
            raise ValidationError("Este registro não pode ser retificado pois ainda não foi transmitido inicialmente!")

        if not self.precisa_atualizar:
            raise ValidationError("Este registro não precisa ser retificado !")

        # Cria o registro de retificação
        self.sped_s2200_id.gerar_registro()

    @api.multi
    def atualizar_contrato_s2206(self):  # TODO
        self.ensure_one()

    @api.multi
    def retificar_contrato_s2300(self):  # TODO
        self.ensure_one()

        # Valida se pode ser retificado
        if not self.sped_s2300_id:
            raise ValidationError("Este registro não pode ser retificado pois ainda não foi transmitido inicialmente!")

        if not self.precisa_atualizar:
            raise ValidationError("Este registro não precisa ser retificado !")

        # Cria o registro de retificação
        self.sped_s2300_id.gerar_registro()

    @api.multi
    def atualizar_contrato_s2306(self):  # TODO
        self.ensure_one()

    @api.multi
    def transmitir(self):  # TODO
        self.ensure_one()

        # # Se o registro S-2190 estiver pendente transmissão   # TODO quando tivermos S-2190
        # if self.sped_s2190_id and self.sped_s2190_id.situacao_esocial in ['1', '3']:
        #     self.sped_s2190_id.transmitir()
        #     return

        # Se o registro S-2200 estiver pendente transmissão
        if self.sped_s2200_id and self.sped_s2200_id.situacao_esocial in ['1', '3']:
            self.sped_s2200_id.transmitir()
            return

        # Se o registro S-2300 estiver pendente transmissão
        if self.sped_s2300_id and self.sped_s2300_id.situacao_esocial in ['1', '3']:
            self.sped_s2300_id.transmitir()
            return

        # Se algum registro S-2206 estiver pendente transmissão
        for s2206 in self.sped_s2206_ids:
            if s2206.situacao_esocial in ['1', '3']:
                s2206.transmitir()
                return

        # Se algum registro S-2306 estiver pendente transmissão
        for s2306 in self.sped_s2306_ids:
            if s2306.situacao_esocial in ['1', '3']:
                s2306.transmitir()
                return

        # Se algum registro S-2299 estiver pendente transmissão
        for s2299 in self.sped_s2299_ids:
            if s2299.situacao_esocial in ['1', '3']:
                s2299.transmitir()
                return

        # Se o registro S-2399 estiver pendente transmissão
        if self.sped_s2399_id and self.sped_s2399_id.situacao_esocial in ['1', '3']:
            self.sped_s2399_id.transmitir()
            return

        # # Se algum registro S-2298 estiver pendente transmissão   # TODO quando tivermos S-2298
        # for s2298 in self.sped_s2298_ids:
        #     if s2298.situacao_esocial in ['1', '3']:
        #         s2298.transmitir()
        #         return

    @api.multi
    def consultar(self):  # TODO
        self.ensure_one()

        # # Se o registro S-2190 estiver transmitida   # TODO quando tivermos S-2190
        # if self.sped_s2190_id and self.sped_s2190_id.situacao_esocial in ['2']:
        #     self.sped_s2190_id.consultar()
        #     return

        # Se o registro S-2200 estiver transmitida
        if self.sped_s2200_id and self.sped_s2200_id.situacao_esocial in ['2']:
            self.sped_s2200_id.consultar()
            return

        # Se o registro S-2300 estiver transmitida
        if self.sped_s2300_id and self.sped_s2300_id.situacao_esocial in ['2']:
            self.sped_s2300_id.consultar()
            return

        # Se algum registro S-2206 estiver transmitida
        for s2206 in self.sped_s2206_ids:
            if s2206.situacao_esocial in ['2']:
                s2206.consultar()
                return

        # Se algum registro S-2306 estiver transmitida
        for s2306 in self.sped_s2306_ids:
            if s2306.situacao_esocial in ['2']:
                s2306.consultar()
                return

        # Se algum registro S-2299 estiver transmitida
        for s2299 in self.sped_s2299_ids:
            if s2299.situacao_esocial in ['2']:
                s2299.consultar()
                return

        # Se o registro S-2399 estiver transmitida
        if self.sped_s2399_id and self.sped_s2399_id.situacao_esocial in ['2']:
            self.sped_s2399_id.consultar()
            return

        # # Se algum registro S-2298 estiver transmitida   # TODO quando tivermos S-2298
        # for s2298 in self.sped_s2298_ids:
        #     if s2298.situacao_esocial in ['2']:
        #         s2298.consultar()
        #         return

    # # Registro S-2200
    # sped_contrato_id = fields.Many2one(
    #     string='SPED Contrato',
    #     comodel_name='sped.esocial.contrato',
    # )
    # # Registro S-2206
    # sped_esocial_alterar_contrato_id = fields.Many2one(
    #     string='Alterar Contrato',
    #     comodel_name='sped.esocial.alteracao.contrato',
    # )
    # precisa_atualizar = fields.Boolean(
    #     string='Precisa atualizar dados?',
    #     related='sped_esocial_alterar_contrato_id.precisa_atualizar',
    # )
    # situacao_esocial = fields.Selection(
    #     selection=[
    #         ('1', 'Pendente'),
    #         ('2', 'Transmitida'),
    #         ('3', 'Erro(s)'),
    #         ('4', 'Sucesso'),
    #         ('5', 'Precisa Retificar'),
    #     ],
    #     string='Situação no e-Social',
    #     related='sped_contrato_id.situacao_esocial',
    #     readonly=True,
    # )
    # situacao_esocial_alteracao = fields.Selection(
    #     selection=[
    #         ('1', 'Precisa Atualizar'),
    #         ('2', 'Transmitida'),
    #         ('3', 'Erro(s)'),
    #         ('4', 'Sucesso'),
    #     ],
    #     string='Situação no e-Social',
    #     related='sped_esocial_alterar_contrato_id.situacao_esocial',
    #     readonly=True,
    # )
    #
    # # Registro S-2300
    # sped_contrato_autonomo_id = fields.Many2one(
    #     string='SPED Contrato',
    #     comodel_name='sped.esocial.contrato.autonomo',
    # )
    # # Registro S-2306
    # sped_esocial_alterar_contrato_autonomo_id = fields.Many2one(
    #     string='Alterar Contrato',
    #     comodel_name='sped.esocial.alteracao.contrato.autonomo',
    # )
    # situacao_esocial_autonomo = fields.Selection(
    #     selection=[
    #         ('1', 'Pendente'),
    #         ('2', 'Transmitida'),
    #         ('3', 'Erro(s)'),
    #         ('4', 'Sucesso'),
    #         ('5', 'Precisa Retificar'),
    #     ],
    #     string='Situação no e-Social',
    #     related='sped_contrato_autonomo_id.situacao_esocial',
    #     readonly=True,
    # )
    # precisa_atualizar_autonomo = fields.Boolean(
    #     string='Precisa atualizar dados?',
    #     related='sped_esocial_alterar_contrato_autonomo_id.precisa_atualizar',
    # )
    #
    # # Registro S-2300
    # sped_contrato_autonomo_id = fields.Many2one(
    #     string='SPED Contrato',
    #     comodel_name='sped.esocial.contrato.autonomo',
    # )
    # # Registro S-2306
    # sped_esocial_alterar_contrato_autonomo_id = fields.Many2one(
    #     string='Alterar Contrato',
    #     comodel_name='sped.esocial.alteracao.contrato.autonomo',
    # )
    # situacao_esocial_autonomo = fields.Selection(
    #     selection=[
    #         ('1', 'Pendente'),
    #         ('2', 'Transmitida'),
    #         ('3', 'Erro(s)'),
    #         ('4', 'Sucesso'),
    #         ('5', 'Precisa Retificar'),
    #     ],
    #     string='Situação no e-Social',
    #     related='sped_contrato_autonomo_id.situacao_esocial',
    #     readonly=True,
    # )
    # precisa_atualizar_autonomo = fields.Boolean(
    #     string='Precisa atualizar dados?',
    #     related='sped_esocial_alterar_contrato_autonomo_id.precisa_atualizar',
    # )
    # admission_type_code = fields.Char(
    #     string='Código do tipo da admissão',
    #     related='admission_type_id.code'
    # )

    # Criar campos que faltam para o eSocial
    admission_type_code = fields.Char(
        string='Código do tipo da admissão',
        related='admission_type_id.code'
    )
    tp_reg_prev = fields.Selection(
        string='Tipo de Regime Previdenciário',
        selection=[
            ('1', 'Regime Geral da Previdência Social - RGPS'),
            ('2', 'Regime Próprio de Previdência Social - RPPS'),
            ('3', 'Remige de Previdência Social no Exterior'),
        ],
    )
    cad_ini = fields.Selection(
        string='Cadastro Inicial de Vínculo',
        selection=[
            ('N', 'Não (Admissão)'),
            ('S', 'Sim (Cadastramento Inicial)'),
        ],
        default='N',
        help='Indicar se o evento se refere a cadastramento inicial de vínculo'
             ' (o ingresso do trabalhador no empregador declarante, por '
             'admissão ou transferência, é anterior à data de início da '
             'obrigatoriedade de envio de seus eventos não periódicos) ou se '
             'refere a uma admissão (o ingresso do trabalhador no empregador'
             ' declarante é igual ou posterior à data de início de '
             'obrigatoriedade de envio de seus eventos não periódicos)',
    )
    tp_reg_jor = fields.Selection(
        string='Regime de Jornada',
        selection=[
            ('1', '1-Submetidos a Horário de Trabalho (Cap. II da CLT)'),
            ('2', '2-Atividade Externa especifica no Inciso I do Art. 62 da CLT'),
            ('3', '3-Funções especificadas no Inciso II do Art. 62 da CLT'),
            ('4', '4-Teletrabalho, previsto no Inciso III do Art. 62 da CLT'),
        ],
    )
    nat_atividade = fields.Selection(
        string='Natureza da Atividade',
        selection=[
            ('1', '1-Trabalho Urbano'),
            ('2', '2-Trabalho Rural'),
        ]
    )
    opc_fgts = fields.Selection(
        string='Optante do FGTS',
        selection=[
            ('1', '1-Optante'),
            ('2', '2-Não Optante'),
        ],
        help='e-Social: S-2200/S-2300 - opcFGTS',
    )
    dt_opc_fgts = fields.Date(
        string='Data de Opção do FGTS',
        help='e-Social: S-2200/S-2300 - dtOpcFgts',
    )
    dsc_sal_var = fields.Char(
        string='Descrição Salário Variável',
        size=255,
        help="e-Social: S-2200/S-2300 - dscSalVar"
             "\nDescrição do salário por tarefa ou variável e como este é "
             "calculado. "
             "\nEx.: Comissões pagas no percentual de 10% sobre as vendas.",
    )
    tp_contr = fields.Selection(
        string='Tipo de Contrato de Trabalho',
        selection=[
            ('1', '1-Prazo indeterminado'),
            ('2', '2-Prazo determinado'),
        ],
        help='e-Social: S-2200 - tpContr',
    )
    clau_assec = fields.Selection(
        string='Contém Cláusula Assecuratória',
        selection=[
            ('S', 'Sim'),
            ('N', 'Não'),
        ],
    )
    tp_jornada = fields.Selection(
        string='Tipo da Jornada',
        selection=[
            ('1', '1-Jornada com horário diário e folga fixos'),
            ('2', '2-Jornada 12x36 (12 horas de trabalho seguidas de 36 horas ininterruptas de descanso'),
            ('3', '3-Jornada com horário diário fixo e folga variável'),
            ('9', '9-Demais tipos de jornada'),
        ],
    )
    dsc_tp_jorn = fields.Char(
        string='Descrição da Jornada',
        size=100,
    )
    tmp_parc = fields.Selection(
        string='Código Tipo Contrato em Tempo Parcial',
        selection=[
            ('0', '0-Não é contrato em tempo parcial'),
            ('1', '1-Limitado a 25 horas semanais'),
            ('2', '2-Limitado a 30 horas semanais'),
            ('3', '3-Limitado a 26 horas semanais'),
        ],
    )
    resignation_cause_id = fields.Many2one(
        comodel_name='sped.motivo_desligamento',
        string='Resignation cause'
    )
    resignation_code = fields.Char(
        related='resignation_cause_id.codigo',
    )
    nr_cert_obito = fields.Char(
        string='Certidão de Óbito',
        size=32,
    )

    evento_esocial = fields.Char(
        string='Evento no esocial',
        help='Definição do Evento do esocial de acordo com a categoria.',
        compute='_compute_evento_esocial',
    )
    salary_unit_code = fields.Char(
        string='Cod. unidade de salario',
        related='salary_unit.code',
    )

    # @api.multi
    # def ativar_contrato(self):
    #     self.ensure_one()
    #
    #     # Se o registro intermediário do S-2200 não existe, criá-lo
    #     if not self.sped_contrato_id:
    #         if self.env.user.company_id.eh_empresa_base:
    #             matriz = self.env.user.company_id.id
    #         else:
    #             matriz = self.env.user.company_id.matriz.id
    #
    #         self.sped_contrato_id = \
    #             self.env['sped.esocial.contrato'].create({
    #                 'company_id': matriz,
    #                 'hr_contract_id': self.id,
    #             })
    #
    #     # Processa cada tipo de operação do S-2200 (Inclusão / Alteração / Exclusão)
    #     # O que realmente precisará ser feito é tratado no método do registro intermediário
    #     self.sped_contrato_id.gerar_registro()
    #
    # @api.multi
    # def write(self, vals):
    #
    #     if self.evento_esocial == 's2200':
    #         self._gerar_tabela_intermediaria_alteracao(vals)
    #
    #     if self.evento_esocial == 's2300':
    #         self._gerar_tabela_intermediaria_alteracao_autonomo(vals)
    #
    #     return super(HrContract, self).write(vals)
    #
    # @api.multi
    # def _gerar_tabela_intermediaria_alteracao(self, vals={}):
    #     # Se o registro intermediário do S-2206 não existe, criá-lo
    #     if not self.sped_esocial_alterar_contrato_id and not \
    #             vals.get('sped_esocial_alterar_contrato_id'):
    #         if self.env.user.company_id.eh_empresa_base:
    #             matriz = self.env.user.company_id.id
    #         else:
    #             matriz = self.env.user.company_id.matriz.id
    #
    #         esocial_alteracao = \
    #             self.env['sped.esocial.alteracao.contrato'].create({
    #                 'company_id': matriz,
    #                 'hr_contract_id': self.id,
    #             })
    #         self.sped_esocial_alterar_contrato_id = esocial_alteracao
    #
    # @api.multi
    # def _gerar_tabela_intermediaria_alteracao_autonomo(self, vals={}):
    #     """
    #     Duplicada
    #     """
    #     if not self.sped_esocial_alterar_contrato_autonomo_id and not \
    #             vals.get('sped_esocial_alterar_contrato_autonomo_id'):
    #         if self.env.user.company_id.eh_empresa_base:
    #             matriz = self.env.user.company_id.id
    #         else:
    #             matriz = self.env.user.company_id.matriz.id
    #
    #         esocial_alteracao = \
    #             self.env['sped.esocial.alteracao.contrato.autonomo'].create({
    #                 'company_id': matriz,
    #                 'hr_contract_id': self.id,
    #             })
    #         self.sped_esocial_alterar_contrato_autonomo_id = esocial_alteracao
    #
    # @api.multi
    # def alterar_contrato(self):
    #     self.ensure_one()
    #
    #     # Se o registro intermediário do S-2206 não existe, criá-lo
    #     if not self.sped_esocial_alterar_contrato_id:
    #         self._gerar_tabela_intermediaria_alteracao()
    #
    #     # Processa cada tipo de operação do S-2206 (Alteração)
    #     # O que realmente precisará ser feito é tratado no método do
    #     # registro intermediário
    #     self.sped_esocial_alterar_contrato_id.gerar_registro()
    #
    #     # Enviar o ultimo registro
    #     # self.sped_esocial_alterar_contrato_id[0].sped_s2200_registro_retificacao[0].transmitir_lote()
    #
    # @api.multi
    # def atualizar_contrato_autonomo(self):
    #     """
    #     Função Duplicada =\
    #     """
    #     self.ensure_one()
    #
    #     sped_esocial_contrato_obj = self.env['sped.esocial.contrato.autonomo']
    #
    #     # Se o registro intermediário não existe, criá-lo
    #     if not self.sped_contrato_autonomo_id:
    #
    #         if self.env.user.company_id.eh_empresa_base:
    #             matriz = self.env.user.company_id.id
    #         else:
    #             matriz = self.env.user.company_id.matriz.id
    #
    #         esocial_contrato_autonomo_id = \
    #             self.env['sped.esocial.contrato.autonomo'].create({
    #                 'company_id': matriz,
    #                 'hr_contract_id': self.id,
    #             })
    #
    #         self.sped_contrato_autonomo_id = esocial_contrato_autonomo_id
    #
    #     # Processa cada tipo de operação do S-2200 (Inclusão / Alteração / Exclusão)
    #     # O que realmente precisará ser feito é tratado no método do registro intermediário
    #     self.sped_contrato_autonomo_id.gerar_registro()
    #
    # @api.multi
    # def alterar_contrato_autonomo(self):
    #     self.ensure_one()
    #
    #     # Se o registro intermediário do S-2206 não existe, criá-lo
    #     if not self.sped_esocial_alterar_contrato_autonomo_id:
    #         self._gerar_tabela_intermediaria_alteracao_autonomo()
    #
    #     # Processa cada tipo de operação do S-2206 (Alteração)
    #     # O que realmente precisará ser feito é tratado no método do
    #     # registro intermediário
    #     self.sped_esocial_alterar_contrato_autonomo_id.gerar_registro()
    #
    @api.multi
    @api.depends('categoria')
    def _compute_evento_esocial(self):
        """
        Validar de acordo com a categoria para definir qual tipo de registro
        sera criado e enviado ao esocial.
        Futuramente será atributo da tabela de categorias.
        """
        categoria_do_s2300 = ['201', '202', '401', '410', '721', '722', '723',
                              '731', '734', '738', '761', '771', '901', '902']
        for record in self:
            if record.categoria in categoria_do_s2300:
                record.evento_esocial = 's2300'
            else:
                record.evento_esocial = 's2200'

    # @api.multi
    # def transmitir_contrato_s2200(self):
    #     self.ensure_one()
    #
    #     # Executa o método Transmitir do registro intermediário
    #     self.sped_contrato_id.transmitir()
    #
    # @api.multi
    # def consultar_contrato_s2200(self):
    #     self.ensure_one()
    #
    #     # Executa o método Consultar do registro intermediário
    #     self.sped_contrato_id.consultar()

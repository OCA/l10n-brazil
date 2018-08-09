# -*- coding: utf-8 -*-
# Copyright 2017 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models, exceptions
from pysped.esocial import ProcessadorESocial
from openerp.exceptions import ValidationError


class HrSalaryRule(models.Model):

    _inherit = 'hr.salary.rule'
    _sql_constraints = [
        ('codigo_unique', 'unique(codigo)', 'Este Código e-Social já existe !'),
        ('identificador_unique', 'unique(identificador)', 'Este Identificador e-Social já existe !'),
    ]

    # Campos de controle S-1010
    sped_rubrica_id = fields.Many2one(
        string='SPED Rubrica',
        comodel_name='sped.esocial.rubrica',
    )
    situacao_esocial = fields.Selection(
        selection=[
            ('0', 'Inativo'),
            ('1', 'Ativo'),
            ('2', 'Precisa Atualizar'),
            ('3', 'Aguardando Transmissão'),
            ('4', 'Aguardando Processamento'),
            ('5', 'Erro(s)'),
            ('9', 'Finalizado'),
        ],
        string='Situação Turno no e-Social',
        related='sped_rubrica_id.situacao_esocial',
        readonly=True,
    )
    precisa_atualizar = fields.Boolean(
        string='Precisa Atualizar',
    )

    # Campos necessários para o e-Social que não existem ainda
    codigo = fields.Char(
        string='Código',
        size=30,
    )
    identificador = fields.Char(
        string='Identificador',
        size=8,
    )
    ini_valid = fields.Many2one(
        string='Válido desde',
        comodel_name='account.period',
        domain=lambda self: self._field_id_domain(),
    )
    alt_valid = fields.Many2one(
        string='Alterado desde',
        comodel_name='account.period',
        domain=lambda self: self._field_id_domain(),
    )
    fim_valid = fields.Many2one(
        string='Válido até',
        comodel_name='account.period',
        domain=lambda self: self._field_id_domain(),
    )
    nat_rubr = fields.Many2one(
        string='Natureza da Rubrica',
        comodel_name='sped.natureza_rubrica',
    )
    tp_rubr = fields.Selection(
        string='Tipo de Rubrica',
        selection=[
            ('1', '1-Vencimento, provento ou pensão'),
            ('2', '2-Desconto'),
            ('3', '3-Informativa'),
            ('4', '4-Informativa dedutora'),
        ],
    )
    cod_inc_cp = fields.Selection(
        string='Incidência Tributária para Previdência Social',
        selection=[
            ('0', 'Não é base de cálculo:'),
            ('1', 'Base de cálculo das contribuições sociais - Salário de Contribuição:'),
            ('3', 'Contribuição descontada do Segurado sobre salário de contribuição:'),
            ('5', 'Outros:'),
            ('9', 'Suspensão de incidência sobre Salário de Contribuição em decorrência de decisão judicial:'),
        ],
    )
    cod_inc_cp_0 = fields.Selection(
        string='Cód.Incid.trib.INSS',
        selection=[
            ('00', '00-Não é base de cálculo'),
            ('01', '01-Não é base de cálculo em função de acordos internacionais de previdência social'),
        ]
    )
    cod_inc_cp_1 = fields.Selection(
        string='Cód.Incid.trib.INSS',
        selection=[
            ('11', '11-Mensal'),
            ('12', '12-13º Salário'),
            ('13', '13-Exclusiva do Empregador - mensal'),
            ('14', '14-Exclusiva do Empregador - 13º salário'),
            ('15', '15-Exclusiva do segurado - mensal'),
            ('16', '16-Exclusiva do segurado - 13º salário'),
            ('21', '21-Salário maternidade mensal pago pelo Empregador'),
            ('22', '22-Salário maternidade - 13º Salário, pago pelo Empregador'),
            ('23', '23-Auxílio doença mensal - Regime Próprio de Previdência Social'),
            ('24', '24-Auxílio doença 13º salário doença - Regime próprio de previdência social'),
            ('25', '25-Salário maternidade mensal pago pelo INSS'),
            ('26', '26-Salário maternidade - 13º salário, pago pelo INSS'),
        ]
    )
    cod_inc_cp_3 = fields.Selection(
        string='Cód.Incid.trib.INSS',
        selection=[
            ('31', '31-Mensal'),
            ('32', '32-13º Salário'),
            ('34', '34-SEST'),
            ('35', '35-SENAT'),
        ]
    )
    cod_inc_cp_5 = fields.Selection(
        string='Cód.Incid.trib.INSS',
        selection=[
            ('51', '51-Salário-família'),
            ('61', '61-Complemento de salário-mínimo - Regime próprio de previdência social'),
        ]
    )
    cod_inc_cp_9 = fields.Selection(
        string='Cód.Incid.trib.INSS',
        selection=[
            ('91', '91-Mensal'),
            ('92', '92-13º Salário'),
            ('93', '93-Salário maternidade'),
            ('94', '94-Salário maternidade 13º salário'),
        ]
    )
    cod_inc_irrf_calculado = fields.Char(
        string='codIncIRRF',
        compute='_compute_cod_inc_irrf_calculado',
        store=True,
    )
    cod_inc_irrf = fields.Selection(
        string='Incidência Tributária para o IRRF',
        selection=[
            ('0', 'Não é rendimento tributável:'),
            ('1', 'Rendimentos tributáveis - base de cálculo do IRRF:'),
            ('3', 'Retenções do IRRF efetuadas sobre:'),
            ('4', 'Deduções da base de cálculo do IRRF:'),
            ('7', 'Isenções do IRRF:'),
            ('8', 'Demandas Judiciais:'),
            ('9', 'Incidência Suspensa decorrente de decisão judicial, relativas a base de cálculo do IRRF sobre:'),
        ],
    )
    cod_inc_irrf_0 = fields.Selection(
        string='Cód.Incid.trib.IRRF',
        selection=[
            ('00', '00-Rendimento não tributável'),
            ('01', '01-Rendimento não tributável em função de acordos internacionais de bitributação'),
        ]
    )
    cod_inc_irrf_1 = fields.Selection(
        string='Cód.Incid.trib.INSS',
        selection=[
            ('11', '11-Remuneração Mensal'),
            ('12', '12-13º Salário'),
            ('13', '13-Férias'),
            ('14', '14-PLR'),
            ('15', '15-Rendimentos Recebidos Acumuladamente - RRA'),
        ]
    )
    cod_inc_irrf_3 = fields.Selection(
        string='Cód.Incid.trib.INSS',
        selection=[
            ('31', '31-Remuneração Mensal'),
            ('32', '32-13º Salário'),
            ('33', '33-Férias'),
            ('34', '34-PLR'),
            ('35', '35-RRA'),
        ]
    )
    cod_inc_irrf_4 = fields.Selection(
        string='Cód.Incid.trib.INSS',
        selection=[
            ('41', '41-Previdência Social Oficial - PSO - Remuner.mensal'),
            ('42', '42-PSO - 13º salário'),
            ('43', '43-PSO - Férias'),
            ('44', '44-PSO - RRA'),
            ('46', '46-Previdência Privada - salário mensal'),
            ('47', '47-Previdência Privada - 13º salário'),
            ('51', '51-Pensão Alimentícia - Remuneração mensal'),
            ('52', '52-Pensão Alimentícia - 13º salário'),
            ('53', '53-Pensão Alimentícia - Férias'),
            ('54', '54-Pensão Alimentícia - PLR'),
            ('55', '55-Pensão Alimentícia - RRA'),
            ('61', '61-Fundo de Aposentadoria Programada Individual - FAPI - Remuneração Mensal'),
            ('62', '62-Fundo de Aposentadoria Programada Individual - FAPI - 13º Salário'),
            ('63', '63-Fundo de Previdência Complementar do Servidor Público - Funpresp - Remuneração mensal'),
            ('64', '64-Fundo de Previdência Complementar do Servidor Público - Funpresp - 13] salário'),
        ]
    )
    cod_inc_irrf_7 = fields.Selection(
        string='Cód.Incid.trib.INSS',
        selection=[
            ('70', '70-Parcela Isenta 65 anos - Remuneração mensal'),
            ('71', '71-Parcela Isenta 65 anos - 13º salário'),
            ('72', '72-Diárias'),
            ('73', '73-Ajuda de custo'),
            ('74', '74-Indenização e rescisão de contrato, inclusive a título de PDV e acidentes de trabalho'),
            ('75', '75-Abono pecuniário'),
            ('76', '76-Pensão, aposentadoria ou reforma por moléstia grave ou acidente em serviço - Remuneração Mensal'),
            ('77', '77-Pensão, aposentadoria ou reforma por moléstia grave ou acidente em serviço - 13º salário'),
            ('78', '78-Valores pagos a titular ou sócio de microempresa ou empresa de pequeno porte, exceto pró-labore e alugueis'),
            ('79', '79-Outras isenções (o nome da rubrica deve ser claro para identificação da natureza dos valores)'),
        ]
    )
    cod_inc_irrf_8 = fields.Selection(
        string='Cód.Incid.trib.INSS',
        selection=[
            ('81', '81-Depósito judicial'),
            ('82', '82-Compensação judicial do ano calendário'),
            ('83', '83-Compensação judicial de anos anteriores'),
        ]
    )
    cod_inc_irrf_9 = fields.Selection(
        string='Cód.Incid.trib.INSS',
        selection=[
            ('91', '91-Remuneração mensal'),
            ('92', '92-13º Salário'),
            ('93', '93-Férias'),
            ('94', '94-PLR'),
            ('95', '95-RRA'),
        ]
    )
    cod_inc_fgts = fields.Selection(
        string='Cód.Incid.para o FGTS',
        selection=[
            ('00', '00-Não é base de cálculo do FGTS'),
            ('11', '11-Base de cálculo do FGTS'),
            ('12', '12-Base de Cálculo do FGTS 13º salário'),
            ('21', '21-Base de Cálculo do FGTS Rescisório (aviso prévio)'),
            ('91', '91-Incidência suspensa em decorrência de decisão judicial'),
        ],
    )
    cod_inc_sind = fields.Selection(
        string='Cód.Incid.para a Contr.Sindical',
        selection=[
            ('00', '00-Não é base de cálculo'),
            ('11', '11-Base de cálculo'),
            ('31', '31-Valor da contribuição sindical laboral descontada'),
            ('91', '91-Incidência suspensa em decorrência de decisão judicial'),
        ],
    )

    @api.onchange('ini_valid')
    def onchange_esocial_periodo_inicial_id(self):
        self.ensure_one()
        if not self.alt_valid or \
                self.alt_valid.date_start < \
                self.ini_valid.date_start:
            self.alt_valid = self.ini_valid

    @api.multi
    def atualizar_rubrica(self):
        self.ensure_one()

        # Se o registro intermediário do S-1010 não existe, criá-lo
        if not self.sped_rubrica_id and self.ini_valid:

            # Verifica se o registro intermediário já existe
            domain = [
                ('company_id', '=', self.env.user.company_id.id),
                ('rubrica_id', '=', self.id),
            ]
            sped_rubrica_id = self.env['sped.esocial.rubrica'].search(domain)
            if sped_rubrica_id:
                self.sped_rubrica_id = sped_rubrica_id
            else:
                self.sped_rubrica_id = \
                    self.env['sped.esocial.rubrica'].create({
                        'company_id': self.env.user.company_id.id,
                        'rubrica_id': self.id,
                    })

        # Processa cada tipo de operação do S-1010 (Inclusão / Alteração / Exclusão)
        # O que realmente precisará ser feito é tratado no método do registro intermediário
        if self.sped_rubrica_id:
            self.sped_rubrica_id.gerar_registro()

    @api.multi
    def write(self, vals):
        self.ensure_one()

        # Lista os campos que são monitorados do Empregador
        campos_monitorados = [
            'ini_valid',        # //eSocial/evtRubrica/infoRubrica//ideRubrica/iniValid
            'alt_valid',        # //eSocial/evtRubrica/infoRubrica//novaValidade/iniValid
            'name',             # //eSocial/evtRubrica/infoRubrica//dadosRubrica/dscRubr
            'nat_rubr',         # //eSocial/evtRubrica/infoRubrica//dadosRubrica/natRubr
            'tp_rubr ',         # //eSocial/evtRubrica/infoRubrica//dadosRubrica/tpRubr
            'cod_inc_cp',       # //eSocial/evtRubrica/infoRubrica//dadosRubrica/codIncCP
            'cod_inc_cp_0',     #
            'cod_inc_cp_1',     #
            'cod_inc_cp_3',     #
            'cod_inc_cp_5',     #
            'cod_inc_cp_9',     #
            'cod_inc_irrf',     # //eSocial/evtRubrica/infoRubrica//dadosRubrica/codIncIRRF
            'cod_inc_irrf_0',   #
            'cod_inc_irrf_1',   #
            'cod_inc_irrf_3',   #
            'cod_inc_irrf_4',   #
            'cod_inc_irrf_7',   #
            'cod_inc_irrf_8',   #
            'cod_inc_irrf_9',   #
            'cod_inc_fgts',     # //eSocial/evtRubrica/infoRubrica//dadosRubrica/codIncIRRF
            'cod_inc_sind',     # //eSocial/evtRubrica/infoRubrica//dadosRubrica/codIncSIND
            'note',             # //eSocial/evtRubrica/infoRubrica//dadosRubrica/observacao
        ]
        precisa_atualizar = False

        # Roda o vals procurando se algum desses campos está na lista
        # Empregador
        if self.sped_rubrica_id and self.situacao_esocial == '1':
            for campo in campos_monitorados:
                if campo in vals:
                    precisa_atualizar = True

            # Se precisa_atualizar == True, inclui ele no vals
            if precisa_atualizar:
                vals['precisa_atualizar'] = precisa_atualizar

        # Grava os dados
        return super(HrSalaryRule, self).write(vals)

    @api.multi
    def transmitir_rubrica(self):
        self.ensure_one()

        # Executa o método Transmitir do registro intermediário
        self.sped_rubrica_id.transmitir()

    @api.multi
    def consultar_rubrica(self):
        self.ensure_one()

        # Executa o método Consultar do registro intermediário
        self.sped_rubrica_id.consultar()

    @api.model
    def _field_id_domain(self):
        """
        Dominio para buscar os registros maiores que 01/2017
        """
        domain = [
            ('date_start', '>=', '2017-01-01'),
            ('special', '=', False)
        ]

        return domain

    @api.depends('cod_inc_irrf', 'cod_inc_irrf_0', 'cod_inc_irrf_1', 'cod_inc_irrf_3',
                 'cod_inc_irrf_4', 'cod_inc_irrf_7', 'cod_inc_irrf_8', 'cod_inc_irrf_9')
    def _compute_cod_inc_irrf_calculado(self):
        for rubrica in self:
            codigo = ''
            if rubrica.cod_inc_irrf == '0':
                codigo = rubrica.cod_inc_irrf_0
            if rubrica.cod_inc_irrf == '1':
                codigo = rubrica.cod_inc_irrf_1
            if rubrica.cod_inc_irrf == '3':
                codigo = rubrica.cod_inc_irrf_3
            if rubrica.cod_inc_irrf == '4':
                codigo = rubrica.cod_inc_irrf_4
            if rubrica.cod_inc_irrf == '7':
                codigo = rubrica.cod_inc_irrf_7
            if rubrica.cod_inc_irrf == '8':
                codigo = rubrica.cod_inc_irrf_8
            if rubrica.cod_inc_irrf == '9':
                codigo = rubrica.cod_inc_irrf_9
            rubrica.cod_inc_irrf_calculado = codigo

# -*- coding: utf-8 -*-
# Copyright 2017 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models, exceptions
from pysped.esocial import ProcessadorESocial
from openerp.exceptions import ValidationError


class ResCompany(models.Model):

    _inherit = 'res.company'

    # Campos de controle S-1000
    sped_empregador_id = fields.Many2one(
        string='SPED Empregador',
        comodel_name='sped.empregador',
    )
    situacao_esocial = fields.Selection(
        selection=[
            ('0', 'Inativa'),
            ('1', 'Ativa'),
            ('2', 'Precisa Atualizar'),
            ('3', 'Aguardando Transmissão'),
            ('9', 'Finalizada'),
        ],
        string='Situação no e-Social',
        related='sped_empregador_id.situacao_esocial',
        readonly=True,
    )

    # Campos de dados diversos
    esocial_tpAmb = fields.Selection(
        string='Ambiente de Transmissão',
        selection=[
            ('1', 'Produção'),
            ('2', 'Produção Restrita'),
        ],
        help='S-1000 (//evtInfoEmpregador/ideEvento/tpAmb)',
    )
    natureza_juridica_id = fields.Many2one(
        string='Tab.21-Natureza Jurídica',
        comodel_name='sped.natureza_juridica',
    )
    ind_coop = fields.Selection(
        string='Indicativo de Cooperativa',
        selection=[
            ('0', 'Não é cooperativa'),
            ('1', 'Cooperativa de Trabalho'),
            ('2', 'Cooperativa de Produção'),
            ('3', 'Outras Cooperativas'),
        ],
        default='0',
    )
    ind_constr = fields.Selection(
        string='Indicativo de Construtora',
        selection=[
            ('0', 'Não é Construtora'),
            ('1', 'Empresa Construtora'),
        ],
        default='0',
    )
    ind_opt_reg_eletron = fields.Selection(
        string='Opta por Registro Eletrônico de Empregados',
        selection=[
            ('0', 'Não optou pelo registro eletrônico de empregados'),
            ('1', 'Optou pelo registro eletrônico de empregados'),
        ],
        default='0',
    )
    ind_ent_ed = fields.Selection(
        string='Entidade sem fins lucrativos',
        selection=[
            ('N', 'Não'),
            ('S', 'Sim'),
        ],
        default='N',
    )
    ind_ett = fields.Selection(
        string='Empr.de Trab.Temporário com registro no Min.Trab.',
        selection=[
            ('N', 'Não'),
            ('S', 'Sim'),
        ],
        default='N',
    )
    nr_reg_ett = fields.Char(
        string='Nº reg. de Trab.Temp. no Min.Trab.',
        size=30,
    )
    esocial_nm_ctt = fields.Char(
        string='Contato',
        size=70,
    )
    esocial_cpf_ctt = fields.Char(
        string='CPF',
        size=11,
    )
    esocial_fone_fixo = fields.Char(
        string='Telefone',
        size=13,
    )
    esocial_fone_cel = fields.Char(
        string='Celular',
        size=13,
    )
    esocial_email = fields.Char(
        string='e-mail',
        size=60,
    )
    cod_lotacao = fields.Char(
        string='Código para Lotação Tributária',
        size=30,
    )
    tp_lotacao_id = fields.Many2one(
        string='Tipo de Lotação Tributária',
        comodel_name='sped.lotacao_tributaria',
    )
    tp_insc_id = fields.Many2one(
        string='Tipo de Inscrição',
        comodel_name='sped.tipos_inscricao',
    )
    nr_insc = fields.Char(
        string='Número de Inscrição',
        size=15,
    )
    fpas_id = fields.Many2one(
        string='Código FPAS',
        comodel_name='sped.codigo_aliquota',
    )
    cod_tercs = fields.Char(
        string='Código de Terceiros',
        size=4,
    )

    # TODO Investigar melhor se o cod_tercs é relacionado a alguma tabela ou não
    # cod_tercs_id = fields.Many2one(
    #     string='Codigo de Terceiros',
    #     comodel_name='sped.classificacao_tributaria',
    #     # domain=[('id', 'in', fpas_id.codigo_tributaria_fpas_ids.ids)],
    # )

    # Ativação do e-Social para a empresa mãe (Registro S-1000)
    # sped_s1000 = fields.Boolean(
    #     string='Ativação eSocial',
    #     compute='_compute_sped_s1000',
    # )
    # sped_s1000_registro = fields.Many2one(
    #     string='Registro S-1000 - Informações do Contribuinte',
    #     comodel_name='sped.registro',
    # )
    # sped_s1000_situacao = fields.Selection(
    #     string='Situação S-1000',
    #     selection=[
    #         ('1', 'Pendente'),
    #         ('2', 'Transmitida'),
    #         ('3', 'Erro(s)'),
    #         ('4', 'Sucesso'),
    #     ],
    #     related='sped_s1000_registro.situacao',
    #     readonly=True,
    # )
    # sped_s1000_data_hora = fields.Datetime(
    #     string='Data/Hora',
    #     related='sped_s1000_registro.data_hora_origem',
    #     readonly=True,
    # )
    esocial_periodo_inicial_id = fields.Many2one(
        string='Período Inicial',
        comodel_name='account.period',
    )
    esocial_periodo_atualizacao_id = fields.Many2one(
        string='Período da Última Atualização',
        comodel_name='account.period',
    )
    esocial_periodo_final_id = fields.Many2one(
        string='Período Inicial',
        comodel_name='account.period',
    )

    # Dados para registro S-1005
    tp_caepf = fields.Selection(
        string='Tipo de CAEPF',
        selection=[
            ('1', 'Contribuinte Invididual'),
            ('2', 'Produtor Rural'),
            ('3', 'Segurado Especial'),
        ],
    )
    reg_pt = fields.Selection(
        string='Opção de Registro de Ponto',
        selection=[
            ('0', 'Não utiliza'),
            ('1', 'Manual'),
            ('2', 'Mecânico'),
            ('3', 'Eletrônico (portaria MTE 1.510/2019)'),
            ('4', 'Não eletrônico alternativo (art. 1º da Portaria MTE 373/2011)'),
            ('5', 'Eletrônico alternativo (art. 2º da Portaria MTE 373/2011)'),
            ('6', 'Eletrônico - outros.'),
        ],
        default='0',
    )
    cont_apr = fields.Selection(
        string='Empresa Contrata Aprendiz',
        selection=[
            ('0', 'Dispensado de acordo com a lei'),
            ('1', 'Dispensado, mesmo que parcialmente, em virtude processo judicial'),
            ('2', 'Obrigado'),
        ],
    )
    cont_ent_ed = fields.Selection(
        string='Usa Entidade Educativa sem fins lucrativos para contratar aprendiz',
        selection=[
            ('S', 'Sim'),
            ('N', 'Não'),
        ],
    )
    info_ent_educ_ids = fields.Many2many(
        string='Entidades Educativas ou de prática desportiva',
        comodel_name='res.partner',
        domain=[('is_company', '=', True)],
    )
    cont_pcd = fields.Selection(
        string='Contrata PCD',
        selection=[
            ('0', 'Dispensado de acordo com a lei'),
            ('1', 'Dispensado, mesmo que parcialmente, em virtude de processo judicial'),
            ('2', 'Com exigibilidade suspensa, mesmo que parcialmente em virtude de Termo de Compromisso firmado com o Ministério do Trabalho'),
            ('9', 'Obrigado'),
        ],
    )

    # @api.depends('sped_s1000_registro')
    # def _compute_sped_s1000(self):
    #     for empresa in self:
    #         empresa.sped_s1000 = True if empresa.sped_s1000_registro else False

    # @api.multi
    # def criar_s1000(self):
    #     self.ensure_one()
    #     if self.sped_s1000_registro:
    #         raise ValidationError('Esta Empresa já ativou o e-Social')
    #
    #     values = {
    #         'tipo': 'esocial',
    #         'registro': 'S-1000',
    #         'ambiente': self.esocial_tpAmb,
    #         'company_id': self.id,
    #         'evento': 'evtInfoEmpregador',
    #         'origem': ('res.company,%s' % self.id),
    #     }
    #
    #     sped_s1000_registro = self.env['sped.registro'].create(values)
    #     self.sped_s1000_registro = sped_s1000_registro

    @api.multi
    def atualizar_esocial(self):
        self.ensure_one()

        # Se o registro intermediário do S-1000 não existe, criá-lo
        if not self.sped_empregador_id:
            self.sped_empregador_id = self.env['sped.empregador'].create({'company_id': self.id})

        # Processa cada tipo de operação do S-1000 (Inclusão / Alteração / Exclusão)
        # O que realmente precisará ser feito é tratado no método do registro intermediário
        self.sped_empregador_id.atualizar_esocial()

        # TODO Incluir registro S-1005 aqui

    # Último envio da Tabela de Estabelecimentos, Obras ou Unidades de Órgãos Públicos (Registro S-1005)
    sped_s1005 = fields.Boolean(
        string='(S-1005) Tabela de Estabelecimentos',
        compute='_compute_sped_s1005',
    )
    sped_s1005_registro = fields.Many2one(
        string='(S-1005) - Tabela de Estabelecimentos',
        comodel_name='sped.registro',
    )
    sped_s1005_situacao = fields.Selection(
        string='Situação S-1005',
        selection=[
            ('1', 'Pendente'),
            ('2', 'Transmitida'),
            ('3', 'Erro(s)'),
            ('4', 'Sucesso'),
        ],
        related='sped_s1005_registro.situacao',
        readonly=True,
    )

    @api.depends('sped_s1005_registro')
    def _compute_sped_s1005(self):
        for empresa in self:
            empresa.sped_s1005 = True if empresa.sped_s1005_registro else False

    @api.multi
    def processador_esocial(self):
        self.ensure_one()

        processador = ProcessadorESocial()
        processador.versao = '2.04.02'

        if self.nfe_a1_file:
            processador.certificado = self.certificado_nfe()

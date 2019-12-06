# -*- coding: utf-8 -*-
# Copyright 2017 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models, exceptions
from pysped.esocial import ProcessadorESocial
from openerp.exceptions import ValidationError
from pybrasil.inscricao.cnpj_cpf import limpa_formatacao


class ResCompany(models.Model):
    _inherit = 'res.company'
    _sql_constraints = [
        ('cod_lotacao unique', 'unique(cod_lotacao)', 'Este Código de Lotação Tributária já existe !'),
    ]

    # Campos de controle S-1000
    sped_empregador_id = fields.Many2one(
        string='SPED Empregador',
        comodel_name='sped.empregador',
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
        string='Situação Empregador no e-Social',
        related='sped_empregador_id.situacao_esocial',
        readonly=True,
    )
    precisa_atualizar = fields.Boolean(
        string='Precisa Atualizar',
    )

    # Campos de controle S-1005
    sped_estabelecimento_id = fields.Many2one(
        string='SPED Estabelecimento',
        comodel_name='sped.estabelecimentos',
    )
    situacao_estabelecimento_esocial = fields.Selection(
        selection=[
            ('0', 'Inativo'),
            ('1', 'Ativo'),
            ('2', 'Precisa Atualizar'),
            ('3', 'Aguardando Transmissão'),
            ('4', 'Aguardando Processamento'),
            ('5', 'Erro(s)'),
            ('9', 'Finalizado'),
        ],
        string='Situação Estabelecimento no e-Social',
        related='sped_estabelecimento_id.situacao_esocial',
        readonly=True,
    )
    precisa_atualizar_estabelecimento = fields.Boolean(
        string='Precisa Atualizar',
    )

    # Campos de controle S-1020
    sped_lotacao_id = fields.Many2one(
        string='SPED Lotacao',
        comodel_name='sped.esocial.lotacao',
    )
    situacao_lotacao_esocial = fields.Selection(
        selection=[
            ('0', 'Inativo'),
            ('1', 'Ativo'),
            ('2', 'Precisa Atualizar'),
            ('3', 'Aguardando Transmissão'),
            ('4', 'Aguardando Processamento'),
            ('5', 'Erro(s)'),
            ('9', 'Finalizado'),
        ],
        string='Situação Lotação Tributária no e-Social',
        related='sped_lotacao_id.situacao_esocial',
        readonly=True,
    )
    precisa_atualizar_lotacao = fields.Boolean(
        string='Precisa Atualizar',
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
        string=u'Natureza Jurídica',
        comodel_name='sped.natureza_juridica',
        help=u'e-Social: Tabela 21 - Natureza Jurídica',
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
    # tp_insc_id = fields.Many2one(
    #     string='Tipo de Inscrição',
    #     comodel_name='sped.tipos_inscricao',
    # )
    # nr_insc = fields.Char(
    #     string='Número de Inscrição',
    #     size=15,
    # )
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
    esocial_periodo_inicial_id = fields.Many2one(
        string='Período Inicial',
        comodel_name='account.period',
        domain=lambda self: self._field_id_domain(),
    )
    esocial_periodo_atualizacao_id = fields.Many2one(
        string='Período da Última Atualização',
        comodel_name='account.period',
        domain=lambda self: self._field_id_domain(),
    )
    esocial_periodo_final_id = fields.Many2one(
        string='Período Final',
        comodel_name='account.period',
        domain=lambda self: self._field_id_domain(),
    )

    # Ativação do e-Social para o Estabelecimento (Registro S-1005)
    estabelecimento_periodo_inicial_id = fields.Many2one(
        string='Período Inicial',
        comodel_name='account.period',
        domain=lambda self: self._field_id_domain(),
    )
    estabelecimento_periodo_atualizacao_id = fields.Many2one(
        string='Período da Última Atualização',
        comodel_name='account.period',
        domain=lambda self: self._field_id_domain(),
    )
    estabelecimento_periodo_final_id = fields.Many2one(
        string='Período Final',
        comodel_name='account.period',
        domain=lambda self: self._field_id_domain(),
    )

    # Ativação do e-Social para a Lotação Tributária (Registro S-1020)
    lotacao_periodo_inicial_id = fields.Many2one(
        string='Período Inicial',
        comodel_name='account.period',
        domain=lambda self: self._field_id_domain(),
    )
    lotacao_periodo_atualizacao_id = fields.Many2one(
        string='Período da Última Atualização',
        comodel_name='account.period',
        domain=lambda self: self._field_id_domain(),
    )
    lotacao_periodo_final_id = fields.Many2one(
        string='Período Final',
        comodel_name='account.period',
        domain=lambda self: self._field_id_domain(),
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

    # Armazena o cnpj/cpf no db sem a formatação para comparação com os registros de Totalização do e-Social
    cnpj_cpf_limpo = fields.Char(
        string='CNPJ/CPF',
        compute='_compute_cnpj_cpf_limpo',
        store=True,
    )

    @api.onchange('esocial_periodo_inicial_id')
    def onchange_esocial_periodo_inicial_id(self):
        self.ensure_one()
        if not self.esocial_periodo_atualizacao_id or \
                self.esocial_periodo_atualizacao_id.date_start < \
                self.esocial_periodo_inicial_id.date_start:
            self.esocial_periodo_atualizacao_id = self.esocial_periodo_inicial_id

    @api.onchange('estabelecimento_periodo_inicial_id')
    def onchange_estabelecimento_periodo_inicial_id(self):
        self.ensure_one()
        if not self.estabelecimento_periodo_atualizacao_id or \
                self.estabelecimento_periodo_atualizacao_id.date_start < \
                self.estabelecimento_periodo_inicial_id.date_start:
            self.estabelecimento_periodo_atualizacao_id = self.estabelecimento_periodo_inicial_id

    @api.onchange('lotacao_periodo_inicial_id')
    def onchange_lotacao_periodo_inicial_id(self):
        self.ensure_one()
        if not self.lotacao_periodo_atualizacao_id or \
                self.lotacao_periodo_atualizacao_id.date_start < \
                self.lotacao_periodo_inicial_id.date_start:
            self.lotacao_periodo_atualizacao_id = self.lotacao_periodo_inicial_id

    @api.depends('cnpj_cpf')
    def _compute_cnpj_cpf_limpo(self):
        for company in self:
            if company.cnpj_cpf:
                company.cnpj_cpf_limpo = limpa_formatacao(company.cnpj_cpf)

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

    @api.multi
    def atualizar_empregador(self):
        self.ensure_one()

        # Se o registro intermediário do S-1000 não existe, criá-lo
        if not self.sped_empregador_id and self.esocial_periodo_inicial_id:

            # Verifica se o registro intermediário já existe
            domain = [('company_id', '=', self.id)]

            sped_empregador_id = self.env['sped.empregador'].search(domain)

            if sped_empregador_id:
                self.sped_empregador_id = sped_empregador_id

            else:
                self.sped_empregador_id = \
                    self.env['sped.empregador'].create({'company_id': self.id})

        # Gerar registro caso nao exista
        if self.sped_empregador_id:
            self.sped_empregador_id.gerar_registro()

    @api.multi
    def atualizar_estabelecimento(self):
        self.ensure_one()

        # Se o registro intermediário do S-1005 não existe, criá-lo
        if not self.sped_estabelecimento_id and self.estabelecimento_periodo_inicial_id:

            # Verifica se o registro intermediário já existe
            matriz = self if self.eh_empresa_base else self.matriz
            domain = [
                ('company_id', '=', matriz.id),
                ('estabelecimento_id', '=', self.id),
            ]
            sped_estabelecimento_id = self.env['sped.estabelecimentos'].search(domain)
            if sped_estabelecimento_id:
                self.sped_estabelecimento_id = sped_estabelecimento_id
            else:
                self.sped_estabelecimento_id = \
                    self.env['sped.estabelecimentos'].create({
                        'company_id': matriz.id,
                        'estabelecimento_id': self.id,
                    })

        # Processa cada tipo de operação do S-1005 (Inclusão / Alteração / Exclusão)
        # O que realmente precisará ser feito é tratado no método do registro intermediário
        if self.sped_estabelecimento_id:
            self.sped_estabelecimento_id.gerar_registro()

    @api.multi
    def atualizar_lotacao(self):
        self.ensure_one()

        # Se o registro intermediário do S-1020 não existe, criá-lo
        if not self.sped_lotacao_id and self.lotacao_periodo_inicial_id:

            # Verifica se o registro intermediário já existe
            matriz = self if self.eh_empresa_base else self.matriz
            domain = [
                ('company_id', '=', matriz.id),
                ('lotacao_id', '=', self.id),
            ]
            sped_lotacao_id = self.env['sped.esocial.lotacao'].search(domain)
            if sped_lotacao_id:
                self.sped_lotacao_id = sped_lotacao_id
            else:
                self.sped_lotacao_id = self.env['sped.esocial.lotacao'].create({
                    'company_id': matriz.id,
                    'lotacao_id': self.id,
                })

        # Processa cada tipo de operação do S-1020 (Inclusão / Alteração / Exclusão)
        # O que realmente precisará ser feito é tratado no método do registro intermediário
        if self.sped_lotacao_id:
            self.sped_lotacao_id.gerar_registro()

    @api.multi
    def processador_esocial(self):
        self.ensure_one()

        processador = ProcessadorESocial()
        processador.versao = '2.04.02'

        if self.nfe_a1_file:
            processador.certificado = self.certificado_nfe()

    @api.multi
    def write(self, vals):
        self.ensure_one()

        # Lista os campos que são monitorados do Empregador
        campos_monitorados = [
            'cnpj_cpf',                         # //eSocial/evtInfoEmpregador/ideEmpregador/nrInsc
            'esocial_periodo_inicial_id',       # //eSocial/evtInfoEmpregador/infoEmpregador//idePeriodo/iniValid
            'esocial_periodo_atualizacao_id',   # //eSocial/evtInfoEmpregador/infoEmpregador//novaValidade/iniValid
            # 'esocial_periodo_final_id',         # //eSocial/evtInfoEmpregador/infoEmpregador//idePeriodo/fimValid
            'legal_name',                       # //eSocial/evtInfoEmpregador/infoEmpregador//infoCadastro/nmRazao
            'classificacao_tributaria_id',      # //eSocial/evtInfoEmpregador/infoEmpregador//infoCadastro/classTrib
            'natureza_juridica_id',             # //eSocial/evtInfoEmpregador/infoEmpregador//infoCadastro/natJurid
            'ind_coop',                         # //eSocial/evtInfoEmpregador/infoEmpregador//infoCadastro/indCoop
            'ind_constr',                       # //eSocial/evtInfoEmpregador/infoEmpregador//infoCadastro/indConstr
            'ind_desoneracao',                  # //eSocial/evtInfoEmpregador/infoEmpregador//infoCadastro/indDesFolha
            'ind_opt_reg_eletron',              # //eSocial/evtInfoEmpregador/infoEmpregador//infoCadastro/indOptRegEletron
            'ind_ent_ed',                       # //eSocial/evtInfoEmpregador/infoEmpregador//infoCadastro/indEntEd
            'ind_ett',                          # //eSocial/evtInfoEmpregador/infoEmpregador//infoCadastro/indEtt
            'nr_reg_ett',                       # //eSocial/evtInfoEmpregador/infoEmpregador//infoCadastro/nrRegEtt
            'esocial_nm_ctt',                   # //eSocial/evtInfoEmpregador/infoEmpregador//infoCadastro/contato/nmCtt
            'esocial_cpf_ctt',                  # //eSocial/evtInfoEmpregador/infoEmpregador//infoCadastro/contato/cpfCtt
            'esocial_fone_fixo',                # //eSocial/evtInfoEmpregador/infoEmpregador//infoCadastro/contato/foneFixo
            'esocial_fone_cel',                 # //eSocial/evtInfoEmpregador/infoEmpregador//infoCadastro/contato/foneCel
            'esocial_email',                    # //eSocial/evtInfoEmpregador/infoEmpregador//infoCadastro/contato/email
            'ind_sitpj',                        # //eSocial/evtInfoEmpregador/infoEmpregador//infoCadastro/infoComplementares/situacaoPj/indSitPJ
        ]
        precisa_atualizar = False

        # Lista os campos que são monitorados do Estabelecimento
        campos_monitorados_estabelecimento = [
            'cnpj_cpf',                                 # //eSocial/evtTabEstab/infoEstab//ideEstab/nrInsc
            'estabelecimento_periodo_inicial_id',       # //eSocial/evtTabEstab/infoEstab//idePeriodo/iniValid
            'estabelecimento_periodo_atualizacao_id',   # //eSocial/evtTabEstab/infoEstab//novaValidade/iniValid
            # 'estabelecimento_periodo_final_id',         # //eSocial/evtTabEstab/infoEstab//idePeriodo/fimValid
            'cnae_main_id',                             # //eSocial/evtTabEstab/infoEstab//dadosEstab/cnaePrep
            # TODO Quando mudar na tabela l10n_br.hr.rat.fap os percentuais de rat/fap, trazer para cá
            'reg_pt',                                   # //eSocial/evtTabEstab/infoEstab//dadosEstab/infoTrab/regPt
            'cont_apr',                                 # //eSocial/evtTabEstab/infoEstab//dadosEstab/infoTrab/infoApr/contApr
            'cont_ent_ed',                              # //eSocial/evtTabEstab/infoEstab//dadosEstab/infoTrab/infoApr/contEntEd
            'info_ent_educ_ids',                        # //eSocial/evtTabEstab/infoEstab//dadosEstab/infoTrab/infoApr/infoEntEduc
            'cont_pcd',                                 # //eSocial/evtTabEstab/infoEstab//dadosEstab/infoTrab/infoPCD
        ]
        precisa_atualizar_estabelecimento = False

        # Lista os campos que são monitorados da Lotação Tributária
        campos_monitorados_lotacao = [
            'cod_lotacao',                      # //eSocial/evtTabLotacao/infoLotacao//ideLotacao/codLotacao
            'lotacao_periodo_inicial_id',       # //eSocial/evtTabLotacao/infoLotacao//ideLotacao/iniValid
            'lotacao_periodo_atualizacao_id',   # //eSocial/evtTabLotacao/infoLotacao//ideLotacao/novaValidade/iniValid
            'tp_lotacao_id',                    # //eSocial/evtTabLotacao/infoLotacao//dadosLotacao/tpLotacao
            'fpas_id',                          # //eSocial/evtTabLotacao/infoLotacao//dadosLotacao/fpasLotacao/fpas
            'cod_tercs',                        # //eSocial/evtTabLotacao/infoLotacao//dadosLotacao/fpasLotacao/codTercs
        ]
        precisa_atualizar_lotacao = False

        # Roda o vals procurando se algum desses campos está na lista
        # Empregador
        if self.sped_empregador_id and self.situacao_esocial == '1':
            for campo in campos_monitorados:
                if campo in vals:
                    vals['precisa_atualizar'] = True

        # Roda o vals procurando se algum desses campos está na lista
        # Estabelecimento
        if self.sped_estabelecimento_id and self.situacao_estabelecimento_esocial == '1':
            for campo in campos_monitorados_estabelecimento:
                if campo in vals:
                    vals['precisa_atualizar_estabelecimento'] = True

        # Roda o vals procurando se algum desses campos está na lista
        # Lotação Tributária
        if self.sped_lotacao_id and self.situacao_lotacao_esocial == '1':
            for campo in campos_monitorados_lotacao:
                if campo in vals:
                    vals['precisa_atualizar_lotacao'] = True

        # Grava os dados
        return super(ResCompany, self).write(vals)

    @api.multi
    def transmitir_empregador(self):
        self.ensure_one()

        # Executa o método Transmitir do registro intermediário
        self.sped_empregador_id.transmitir()

    @api.multi
    def consultar_empregador(self):
        self.ensure_one()

        # Executa o método Consultar do registro intermediário
        self.sped_empregador_id.consultar()

    @api.multi
    def transmitir_estabelecimento(self):
        self.ensure_one()

        # Executa o método Transmitir do registro intermediário
        self.sped_estabelecimento_id.transmitir()

    @api.multi
    def consultar_estabelecimento(self):
        self.ensure_one()

        # Executa o método Consultar do registro intermediário
        self.sped_estabelecimento_id.consultar()

    @api.multi
    def transmitir_lotacao(self):
        self.ensure_one()

        # Executa o método Transmitir do registro intermediário
        self.sped_lotacao_id.transmitir()

    @api.multi
    def consultar_lotacao(self):
        self.ensure_one()

        # Executa o método Consultar do registro intermediário
        self.sped_lotacao_id.consultar()

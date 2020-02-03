# -*- coding: utf-8 -*-
# (c) 2019 Hendrix Costa <hendrix.costa@abgf.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from __future__ import (
    division, print_function, unicode_literals, absolute_import
)

import base64
import re

from openerp import api, fields, models
from pybrasil.valor import formata_valor

from .arquivo_dirf import DIRF, Beneficiario, ValoresMensais, \
    InformacoesComplementares


class L10nBrHrDirf(models.Model):
    _name = b'hr.dirf'
    _inherit = [b'abstract.arquivos.governo.workflow', b'mail.thread']
    _order = b'ano_referencia DESC, company_id ASC'

    name = fields.Char(
        compute="_compute_name",
        store=True,
        index=True
    )

    contract_ids = fields.Many2many(
        string='Contratos',
        comodel_name='hr.contract',
    )

    employee_ids = fields.Many2many(
        string=u'Funcionários',
        comodel_name='hr.employee',
        context={'active_test': False},
    )

    company_id = fields.Many2one(
        comodel_name='res.company',
        string=u'Empresa',
        readonly=True,
        states={'draft': [('readonly', False)]},
    )

    ano_referencia = fields.Char(
        string=u'Ano Referência',
        size=4,
        readonly=True,
        states={'draft': [('readonly', False)]},
        default=fields.Date.from_string(fields.Date.today()).year
    )

    ano_calendario = fields.Char(
        string=u'Ano Calendário',
        size=4,
        readonly=True,
        states={'draft': [('readonly', False)]},
        default=fields.Date.from_string(fields.Date.today()).year
    )

    dirf = fields.Text(
        string=u'Prévia da DIRF',
        readonly=True,
        states={'draft': [('readonly', False)]},
    )

    numero_recibo = fields.Char(
        string='Número do recibo',
        help='Número do recibo a retificar. '
             'Não preencher se não for arquivo retificadora',
    )

    responsible_partner_id = fields.Many2one(
        comodel_name='res.partner',
        string=u'Usuário Responsável',
        readonly=True,
        states={'draft': [('readonly', False)]},
    )

    retificadora = fields.Boolean(string='Retificadora?')

    responsible_ddd = fields.Char(string='DDD')

    responsible_telefone = fields.Char(string='Telefone')
    
    responsible_ramal = fields.Char(string='Ramal')

    responsible_cnpj_cpf = fields.Char(string='CPF Responsável')

    natureza_declarante = fields.Selection(
        selection = [
            ('0','0 - Pessoa jurídica de direito privado'),
            ('1','1 - Órgãos, autarquias e fundações da administração '
                 'pública federal'),
            ('2','2 - Órgãos, autarquias e fundações da administração '
                 'pública estadual, municipal ou do Distrito Federal'),
            ('3','3 - Empresa pública ou sociedade de economia mista federal'),
            ('4','4 - Empresa pública ou sociedade de economia mista estadual,'
                 ' municipal ou do Distrito Federal'),
            ('8','8 - Entidade com alteração de natureza jurídica '
                 '(uso restrito)'),
        ],
        string='Natureza do Declarante',
        required=True,
    )

    codigo_receita = fields.Selection(
        selection=[
            ('0561','0561'),
            ('0588','0588'),
            ('3223','3223'),
        ],
        string='Código da Receita',
    )

    responsible_partner_cnpj_id = fields.Many2one(
        comodel_name='res.partner',
        string=u'Responsável pelo CNPJ',
        readonly=True,
        states={'draft': [('readonly', False)]},
    )

    dirf_file = fields.Binary(
        string='Arquivo DIRF', readonly=True
    )

    dirf_filename = fields.Char(string="Filename", readonly=True)

    @api.onchange('responsible_partner_id')
    def set_contato(self):
        """
        """
        for record in self:
            if record.responsible_partner_id:
                record.responsible_ddd = \
                    re.sub('[^0-9]', '',
                           record.responsible_partner_id.phone or '')[:2]
                record.responsible_telefone = \
                    re.sub('\(.*\)', '',
                           record.responsible_partner_id.phone or '').strip()
                record.responsible_ramal = \
                    re.sub('[^0-9]', '',
                           record.responsible_partner_id.phone or '')[-4:]
            else:
                record.responsible_ddd = ''
                record.responsible_telefone = ''
                record.responsible_ramal = ''

    @api.onchange('responsible_partner_cnpj_id')
    def set_responsible_partner_cnpj(self):
        """
        """
        for record in self:
            if record.responsible_partner_cnpj_id:
                record.responsible_cnpj_cpf = \
                    record.responsible_partner_cnpj_id.cnpj_cpf
            else:
                record.responsible_cnpj_cpf = ''

    @api.depends('company_id', 'ano_referencia')
    def _compute_name(self):
        """
        """
        for record in self:
            if record.company_id and record.ano_referencia:
                record.name = \
                    'DIRF - {} - {}'.format(
                        record.ano_referencia, record.company_id.name)

    @api.multi
    def buscar_funcionarios(self):
        """
        Preencher Funcionários que irao compor a DIRF
        """
        for record in self:

            if record.company_id:

                tipoFolha = ['normal', 'ferias', 'decimo_terceiro', 'rescisao']

                #  Buscar todos holerites do ano
                holerites_no_ano = self.buscar_holerites(
                    record.ano_referencia, record.company_id,
                    tipo_folha=tipoFolha)

                # DIRF para todos funcionarios que tiveram rendimentos
                record.employee_ids = holerites_no_ano.mapped('employee_id')

    @api.multi
    def buscar_holerites(self, ano, company_id, employee_id=False, tipo_folha=[]):
        """
        Buscar holerites de determinado ano e empresa
        """
        self.ensure_one()

        domain = [
            ('ano', '=', int(ano)),
            ('is_simulacao', '=', False),
            ('company_id', '=', company_id.id),
            ('state', 'in', ['done', 'verify']),
        ]
        if employee_id:
            domain.append(('employee_id', '=', employee_id.id))

        if tipo_folha:
            domain.append(('tipo_de_folha', 'in', tipo_folha))

        return self.env['hr.payslip'].search(domain)

    @api.multi
    def get_valor_13(self, holerites_ids, rubrica):
        """
        """
        # Filtrar holerites de acordo com paramentros da função
        decimo_terceiro_ids = holerites_ids.filtered(
            lambda x: x.tipo_de_folha in ['decimo_terceiro'])

        rescisao_ids = holerites_ids.filtered(
            lambda x: x.tipo_de_folha in ['rescisao'])

        if rubrica[1] == 'BASE_IR':
            baseir_13 = \
                sum(decimo_terceiro_ids.mapped('rendimentos_tributaveis'))
            baseir_rescisao = sum(rescisao_ids.mapped('line_ids').filtered(
                lambda x: x.code == 'PROP13').mapped('total'))
            return baseir_13 + baseir_rescisao

        # Quando for informacao do dependente buscar campo
        if rubrica[1] == 'INFO_DEPENDENTE':
            return sum(decimo_terceiro_ids.mapped('valor_total_dependente'))

        # Buscar a rubrica especifica para cada tipo de holerite
        line_13_ids = sum(decimo_terceiro_ids.mapped('line_ids').filtered(
            lambda x: x.code in rubrica[1]).mapped('total'))

        line_rescisao_ids = sum(rescisao_ids.mapped('line_ids').filtered(
            lambda x: x.code in
                      ['{}_13'.format(x) for x in rubrica[1]]).mapped('total'))

        return line_13_ids + line_rescisao_ids

    @api.multi
    def get_valor_mes(self, holerites_ids, mes, rubrica):
        """
        """
        # Tipos validos para holerites mensais
        tipo = ['normal', 'ferias', 'rescisao']

        # Filtrar holerites de acordo com paramentros da função
        holerites_ids = holerites_ids.filtered(
            lambda x: x.tipo_de_folha in tipo and x.mes_do_ano == mes)

        # Se nao encontrou holerites
        if not holerites_ids:
            return 0

        # Quando for a BASE de rendimentos tributáveis, buscar campo
        if rubrica[1] == 'BASE_IR':
            return sum(holerites_ids.mapped('rendimentos_tributaveis'))

        # Quando for informacao do dependente buscar campo
        if rubrica[1] == 'INFO_DEPENDENTE':
            return sum(holerites_ids.mapped('valor_total_dependente'))

        # Buscar a rubrica especifica entre as linhas do holerite
        line_ids = holerites_ids.mapped('line_ids').filtered(
            lambda x: x.code in rubrica[1])

        return sum(line_ids.mapped('total'))

    def ocorrencia_rubrica_no_ano(self, code, RUBRICAS_DIRF, rubricas_ativas):

        # Verificar se eh uma rubrica e nao um campo
        if code[0] in [x[0] for x in RUBRICAS_DIRF]:

            # Se for rubrica necessariamente deverá esta em rubricas ativas
            return any([x in rubricas_ativas for x in code[1]])

        return True

    @api.multi
    def populate_beneficiario(self, dirf, beneficiario, employee_id,
                              ano, company_id):
        """
        :param beneficiario:
        :param employee_id:
        :param ano:
        :return:
        """

        # Buscar Holerites do ano do funcionário
        tipoFolha = ['normal', 'ferias', 'decimo_terceiro', 'rescisao']
        holerites_ids = self.buscar_holerites(
            ano, company_id, employee_id, tipoFolha)

        rubricas_ativas = holerites_ids.mapped('line_ids.salary_rule_id.code')

        RUBRICAS_DIRF = [
            ('RTPO', ['INSS', 'PSS'], 20),
            ('RTIRF', ['IRPF', 'IRPF_FERIAS'], 40),
            ('RTPA', ['PENSAO_ALIMENTICIA_PORCENTAGEM',
                'PENSAO_ALIMENTICIA_PORCENTAGEM_FERIAS'], 60),
            ('RIDAC', ['DIARIAS_VIAGEM', 'AUXILIO_MORADIA',
                       '1/12_GRATIFICACAO_NATALINA',
                       '1/12_GRATIFICACAO_NATALINA_MES_ANTERIOR',
                       '1/12_DE_1/3_FERIAS'], 50),
        ]

        CAMPOS_DIRF = [
            ('RTRT', 'BASE_IR', 10),
            ('RTDP', 'INFO_DEPENDENTE', 30),
        ]

        valoresMensais = RUBRICAS_DIRF + CAMPOS_DIRF
        valoresMensais.sort(key=lambda x: x[2])

        for code in valoresMensais:

            # if code[0] in [x[0] for x in RUBRICAS_DIRF] and \
            #         not code[1] in rubricas_ativas:
            #     continue

            if not self.ocorrencia_rubrica_no_ano(
                    code, RUBRICAS_DIRF, rubricas_ativas):
                continue

            vm = ValoresMensais()
            vm.identificador_de_registro_mensal = code[0]
            vm.janeiro = self.get_valor_mes(holerites_ids, 1, code)
            vm.fevereiro = self.get_valor_mes(holerites_ids, 2, code)
            vm.marco = self.get_valor_mes(holerites_ids, 3, code)
            vm.abril = self.get_valor_mes(holerites_ids, 4, code)
            vm.maio = self.get_valor_mes(holerites_ids, 5, code)
            vm.junho = self.get_valor_mes(holerites_ids, 6, code)
            vm.julho = self.get_valor_mes(holerites_ids, 7, code)
            vm.agosto = self.get_valor_mes(holerites_ids, 8, code)
            vm.setembro = self.get_valor_mes(holerites_ids, 9, code)
            vm.outubro = self.get_valor_mes(holerites_ids, 10, code)
            vm.novembro = self.get_valor_mes(holerites_ids, 11, code)
            vm.dezembro = self.get_valor_mes(holerites_ids, 12, code)
            vm.decimo_terceiro = self.get_valor_13(holerites_ids, code)

            if any([vm.janeiro, vm.fevereiro, vm.marco, vm.abril, vm.maio,
                    vm.junho, vm.julho, vm.agosto, vm.setembro, vm.outubro,
                    vm.novembro, vm.dezembro, vm.decimo_terceiro]):
                beneficiario.add_valores_mensais(vm)

        #
        # Rendimentos Isentos
        #
        valor_rio, descricao_rio = \
            self.get_rendimentos_isentos_anuais(holerites_ids)

        if valor_rio or descricao_rio:
            beneficiario.valor_pago_ano_rio = valor_rio
            beneficiario.descricao_rendimentos_isentos = descricao_rio

        #
        #
        #
        mensagem_informacao_complementar = ''

        #
        # Beneficiario de Pensao
        #
        if 'PENSAO_ALIMENTICIA_PORCENTAGEM' in rubricas_ativas:

            payslip_line_ids = holerites_ids.mapped('line_ids')

            lines_ids = payslip_line_ids.filtered(
                lambda x: x.salary_rule_id.code in
                          ['PENSAO_ALIMENTICIA_PORCENTAGEM'])

            partner_id = lines_ids.mapped('partner_id')
            beneficiario.cpf_infpa = partner_id.cnpj_cpf
            beneficiario.nome_infpa = partner_id.name
            beneficiario.data_nascimento_infpa = '19701001'
            beneficiario.relacao_dependencia_infpa = '03'
            beneficiario.identificacao_alimentado_bpfdec = 'S'

        #
        # Informacoes Complementares (Quadro 7) PENSAO
        #
            RUBRICAS_PENSAO = [
                'PENSAO_ALIMENTICIA_PORCENTAGEM',
                'PENSAO_ALIMENTICIA_PORCENTAGEM_FERIAS_FERIAS',
            ]

            total_pensao = 0
            total_pensao_13 = 0

            for holerite_id in holerites_ids:

                line_pensao = holerite_id.line_ids.filtered(
                        lambda x: x.salary_rule_id.code in RUBRICAS_PENSAO)

                if holerite_id.tipo_de_folha not in ['decimo_terceiro']:
                    total_pensao += sum(line_pensao.mapped('total'))
                else:
                    total_pensao_13 += sum(line_pensao.mapped('total'))

            if total_pensao or total_pensao_13:

                dados = {
                    'nome': partner_id.name,
                    'cpf': partner_id.cnpj_cpf,
                    'total_pensao': formata_valor(total_pensao),
                    'total_pensao_13': formata_valor(total_pensao_13),
                }

                mensagem = \
                    '-Pensao alimenticia: ' \
                    '{nome}, CPF {cpf} TOTAL: R$ {total_pensao} ' \
                    'Sobre o 13o Salario RS {total_pensao_13};  '

                mensagem_informacao_complementar += mensagem.format(**dados)


        #
        # Informacoes Complementares (Quadro 7) AUXILIO SAUDE
        #

        RUBRICAS_SAUDE = [
            'REMBOLSO_SAUDE',
            'REEMBOLSO_AUXILIO_SAUDE_MES_ANTERIOR',
            'AUXILIO_SAUDE_DIRETOR',
        ]

        if 'REMBOLSO_SAUDE' in rubricas_ativas:

            line_ids_saude = holerites_ids.mapped('line_ids').filtered(
                lambda x: x.code in RUBRICAS_SAUDE)

            total_saude = sum(line_ids_saude.mapped('total'))

            dados = {
                'nome': employee_id.name,
                'cpf': employee_id.cpf,
                'total_saude': formata_valor(total_saude),
            }

            mensagem = '-Reembolso de Saúde: R$ {total_saude};  '

            mensagem_informacao_complementar += mensagem.format(**dados)

        #
        # Informacoes Complementares (Quadro 7) Tributos Isentos
        #
        rubricas_isentas = filter(lambda x: x[0] == 'RIDAC', RUBRICAS_DIRF)[0]

        mensagem_isentos = []

        for rubrica in rubricas_isentas[1]:

            if rubrica not in rubricas_ativas:
                continue

            line_ids = holerites_ids.mapped('line_ids').filtered(
                lambda x: x.code in rubrica)
            total = formata_valor(sum(line_ids.mapped('total')))
            name = line_ids[0].name

            if total:
                mensagem_isentos.append(' {}: {}'.format(name, total))

        if mensagem_isentos:
            mensagem_isentos = \
                '-Tributos Isentos: {};'.format(','.join(mensagem_isentos))
            mensagem_informacao_complementar += mensagem_isentos

        if mensagem_informacao_complementar:
            inf = InformacoesComplementares()
            inf.cpf_inf = employee_id.cpf
            inf.informacoes_complementares = mensagem_informacao_complementar
            dirf.add_informarmacaoComplementar(inf)

    @api.multi
    def get_rendimentos_isentos_anuais(self, holerites_ids):
        """
        :param holerites_ids:
        :return:
        """
        holerites_ids = holerites_ids.filtered(
            lambda x: x.tipo_de_folha in ['rescisao', 'ferias'])

        RUBRICAS_FERIAS_RECISAO = [
            'PROP_FERIAS',
            'PROP_1/3_FERIAS',
            'FERIAS_VENCIDAS',
            'FERIAS_VENCIDAS_1/3',
            'ABONO_PECUNIARIO',
            '1/3_ABONO_PECUNIARIO',
        ]

        total = sum(holerites_ids.mapped('line_ids').filtered(
            lambda x: x.code in RUBRICAS_FERIAS_RECISAO).mapped('total')) or 0

        descricao = holerites_ids.mapped('line_ids').filtered(
            lambda x: x.code in RUBRICAS_FERIAS_RECISAO).mapped('name') or ''

        descricao = ', '.join(descricao)

        return total, descricao

    @api.multi
    def atualizar_valores_holerites(self):
        """
        Função para Atualizar todos valores de IR dos holerites
        """

        tx_deducao = self.env['l10n_br.hr.income.tax.deductable.amount.family']

        valor_por_dependente = tx_deducao.search([
            ('year', '=', self.ano_referencia)], limit=1,
        ).amount or 0

        for employee_id in self.employee_ids:
            holerites_ids = self.buscar_holerites(
                self.ano_referencia, self.company_id, employee_id)

            for holerite_id in holerites_ids:
                holerite_id.atualizar_valores(valor_por_dependente)

    @api.multi
    def gerar_dirf(self):
        """
        Método principal da geração da DIRF
        """
        self.ensure_one()

        dirf = DIRF()

        # Definir cabeçalho
        dirf.ano_referencia = self.ano_referencia
        dirf.ano_calendario = self.ano_calendario

        # DIRF ano referencia 2018 ano base 2017 == Q84FV63
        if self.ano_referencia == '2018':
            dirf.identificador_de_estrutura_do_leiaute = 'Q84FV63'

        # DIRF ano referencia 2019 ano base 2018 == T17BS45
        if self.ano_referencia == '2019':
            dirf.identificador_de_estrutura_do_leiaute = 'T17BS45'

        # DIRF ano referencia 2020 ano base 2019 == AT65HD8
        if self.ano_referencia == '2020':
            dirf.identificador_de_estrutura_do_leiaute = 'AT65HD8'

        dirf.indicador_de_retificadora = 'S' if self.retificadora else 'N'
        dirf.numero_do_recibo = self.numero_recibo

        # Definir responsavel
        dirf.cpf_respo = self.responsible_partner_id.cnpj_cpf
        dirf.nome_respo = self.responsible_partner_id.name
        dirf.ddd_respo = self.responsible_ddd
        dirf.telefone_respo = self.responsible_telefone
        dirf.ramal_respo = self.responsible_ramal
        dirf.correio_eletronico = self.responsible_partner_id.email

        # Identificação de Pessoa Juridica
        dirf.cnpj_decpj = self.company_id.cnpj_cpf
        dirf.nome_empresarial = self.company_id.legal_name
        dirf.natureza_do_declarante = self.natureza_declarante
        dirf.cpf_responsavel = self.responsible_cnpj_cpf
        dirf.data_do_evento_decpj = ''

        # Identificação do Código da receita - IDREC
        dirf.codigo_da_receita = '0561'

        # Preencher beneficiarios
        for employee_id in self.employee_ids:
            beneficiario = Beneficiario()
            beneficiario.cpf_bpfdec = \
                re.sub('[^0-9]', '', str(employee_id.cpf))
            beneficiario.nome_bpfdec = employee_id.name
            self.populate_beneficiario(
                dirf, beneficiario, employee_id, self.ano_referencia,
                self.company_id)

            grupo = dirf.get_grupoFuncionarioPorCodigoReceita(
                employee_id.contract_id.codigo_guia_darf)
            grupo.add_beneficiario(beneficiario)

        self.dirf = str(dirf)

        # Gera o arquivo apartir do txt do grrf no temp do sistema
        nome_arquivo = 'DIRF{}{}.txt'.format(
            self.ano_referencia, self.company_id.name)

        self.dirf_file = base64.b64encode(str(dirf))

        self.dirf_filename = nome_arquivo

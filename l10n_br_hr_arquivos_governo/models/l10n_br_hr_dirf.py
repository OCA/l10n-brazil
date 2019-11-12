# -*- coding: utf-8 -*-
# (c) 2019 Hendrix Costa <hendrix.costa@abgf.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from __future__ import (
    division, print_function, unicode_literals, absolute_import
)

from openerp import api, fields, models
from openerp.exceptions import Warning

from .arquivo_dirf import DIRF, Beneficiario, ValoresMensais

import re


class L10nBrHrDirf(models.Model):
    _name = b'hr.dirf'
    _inherit = [b'abstract.arquivos.governo.workflow', b'mail.thread']
    _order = b'ano DESC, company_id ASC'

    name = fields.Char(
        compute="_compute_name",
        store=True,
        index=True
    )

    contract_ids = fields.Many2many(
        string='Contratos',
        comodel_name='hr.contract',
    )

    company_id = fields.Many2one(
        comodel_name='res.company',
        string=u'Empresa',
        readonly=True,
        states={'draft': [('readonly', False)]},
    )

    ano = fields.Char(
        string=u'Ano',
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

    retificadora = fields.Boolean(string='Retificadora?')

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

    responsible_ddd = fields.Char(string='DDD')

    responsible_telefone = fields.Char(string='Telefone')
    
    responsible_ramal = fields.Char(string='Ramal')

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

    @api.onchange('responsible_partner_id')
    def set_contato(self):
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

    @api.depends('company_id', 'ano')
    def _compute_name(self):
        for record in self:
            if record.company_id and record.ano:
                record.name = \
                    'DIRF - {} - {}'.format(record.ano, record.company_id.name)

    @api.multi
    def buscar_contratos(self):
        """
        Preencher contratos que irao compor a DIRF
        """
        for record in self:

            if record.company_id:
                inicio_ano = '01-01-{}'.format(record.ano)

                domain = [
                    '|',
                    ('date_end', '>', inicio_ano),
                    ('date_end','=', False),
                    ('tipo', '!=', 'autonomo'),
                    ('company_id', '=', record.company_id.id)
                ]

                record.contract_ids = self.env['hr.contract'].search([domain])

    @api.multi
    def buscar_holerites(self, contract_id, ano):
        """
        """
        for record in self:
            domain = [
                ('contract_id', '=', contract_id.id),
                ('ano', '=', int(ano)),
                ('tipo_de_folha','in', ['normal', 'decimo_terceiro', 'rescisao']),
                ('is_simulacao', '=', False),
                ('state', 'in', ['done', 'verify']),
            ]
            return self.env['hr.payslip'].search(domain)


    @api.multi
    def get_valor_mes(self, holerites_ids, mes, rubrica, tipo='normal'):
        """
        """
        holerites_ids = \
            holerites_ids.filtered(lambda x: x.tipo_de_folha in tipo)
        if tipo == 'decimo_terceiro':
            total = 0
            if rubrica[1] == 'INFO_DEPENDENTE':
                for holerite_id in holerites_ids:
                    total = holerite_id.valor_total_dependente
            else:
                total = sum(holerites_ids.mapped('line_ids').filtered(
                    lambda x: x.code == rubrica[1]).mapped('total'))
        else:
            holerite_id = \
                holerites_ids.filtered(lambda x: x.mes_do_ano2 == mes)
            if len(holerite_id) > 1:
                raise Warning(
                    'Mais de 1 Holerite encontrado para o mesmo Funcionário'
                    ' no mesmo período.\n{} - {}/{}'.format(
                    holerite_id[0].employee_id.name, mes, self.ano))
            if not holerite_id:
                return False
            if rubrica[1] == 'INFO_DEPENDENTE':
                total = holerite_id.valor_total_dependente
            else:
                line_id = holerite_id.line_ids.filtered(lambda x: x.code == rubrica[1])
                total = line_id.total

        return total



    @api.multi
    def popular_dependente(self):
        """
        """
        data = {}

        domain = [
            ('year', '=', self.ano),
        ]

        valor_por_dependente = self.env['l10n_br.hr.income.tax.deductable.amount.family']. \
                                   search(domain, limit=1).amount or 0

        for contract_id in self.contract_ids:
            holerites_ids = self.buscar_holerites(contract_id, self.ano)
            for holerite_id in holerites_ids:
                if holerite_id:
                    dados = holerite_id.get_dependente(valor_por_dependente)
                    data['quantidade_dependente'] = dados.get('quantidade_dependentes')
                    data['valor_total_dependente'] = dados.get('quantidade_dependentes') * \
                                                     dados.get('valor_por_dependente')
                    holerite_id.write(data)

    @api.multi
    def populate_beneficiario(self, beneficiario, contract_id, ano):
        """
        :param beneficiario:
        :param contract_id:
        :param ano:
        :return:
        """
        for record in self:

            RUBRICAS_DIRF = [
                ('RTRT', 'BASE_INSS'),
                ('RTPO', 'INSS'),
                ('RTDP', 'INFO_DEPENDENTE'),
                ('RIDAC', 'DIARIAS_VIAGEM'),
                ('RTIRF', 'IRPF'),
            ]

            holerites_ids = self.buscar_holerites(contract_id, ano)

            codes = holerites_ids.mapped('line_ids.code')

            for rubrica in RUBRICAS_DIRF:
                #if rubrica[1] not in codes and rubrica not in ['INFO_DEPENDENTE']:
                #    continue

                valores_mensais = ValoresMensais()
                valores_mensais.identificador_de_registro_mensal = rubrica[0]
                valores_mensais.janeiro = self.get_valor_mes(holerites_ids, 1, rubrica)
                valores_mensais.fevereiro = self.get_valor_mes(holerites_ids, 2, rubrica)
                valores_mensais.marco = self.get_valor_mes(holerites_ids, 3, rubrica)
                valores_mensais.abril = self.get_valor_mes(holerites_ids, 4, rubrica)
                valores_mensais.maio = self.get_valor_mes(holerites_ids, 5, rubrica)
                valores_mensais.junho = self.get_valor_mes(holerites_ids, 6, rubrica)
                valores_mensais.julho = self.get_valor_mes(holerites_ids, 7, rubrica)
                valores_mensais.agosto = self.get_valor_mes(holerites_ids, 8, rubrica)
                valores_mensais.setembro = self.get_valor_mes(holerites_ids, 9, rubrica)
                valores_mensais.outubro = self.get_valor_mes(holerites_ids, 10, rubrica)
                valores_mensais.novembro = self.get_valor_mes(holerites_ids, 11, rubrica)
                valores_mensais.dezembro = self.get_valor_mes(holerites_ids, 12, rubrica)
                valores_mensais.decimo_terceiro = self.get_valor_mes(holerites_ids, 13, rubrica, tipo='decimo_terceiro')
                beneficiario.add_valores_mensais(valores_mensais)

            beneficiario.valor_pago_ano_rio, beneficiario.descricao_rendimentos_isentos = \
                self.get_valor_rio(holerites_ids)

    @api.multi
    def get_valor_rio(self, holerites_ids):

        holerites_ids = holerites_ids.filtered(lambda x: x.tipo_de_folha in 'rescisao')

        RUBRICAS_FERIAS_RECISAO = [
            'PROP_FERIAS',
            'PROP_1/3_FERIAS',
            'FERIAS_VENCIDAS',
            'FERIAS_VENCIDAS_1/3',
        ]

        total = sum(
            holerites_ids.mapped('line_ids').
                filtered(lambda x: x.code in RUBRICAS_FERIAS_RECISAO).mapped('total')) or 0

        descricao = holerites_ids.mapped('line_ids').\
                        filtered(lambda x: x.code in RUBRICAS_FERIAS_RECISAO).mapped('name') or ''

        return total, ', '.join(descricao)

    @api.multi
    def gerar_dirf(self):
        """
        """
        self.ensure_one()

        dirf = DIRF()

        # Definir cabeçalho
        dirf.ano_referencia = self.ano
        dirf.ano_calendario = self.ano
        dirf.indicador_de_retificadora = 'S' if self.retificadora else 'N'
        dirf.numero_do_recibo = self.numero_recibo
        print(dirf.DIRF)

        # Definir responsavel
        dirf.cpf_respo = self.responsible_partner_id.cnpj_cpf
        dirf.nome_respo = self.responsible_partner_id.name
        dirf.ddd_respo = self.responsible_ddd
        dirf.telefone_respo = self.responsible_telefone
        dirf.ramal_respo = self.responsible_ramal
        dirf.correio_eletronico = self.responsible_partner_id.email
        print(dirf.RESPO)

        # Identificação de Pessoa Juridica
        dirf.cnpj_decpj = self.company_id.cnpj_cpf
        dirf.nome_empresarial = self.company_id.legal_name
        dirf.natureza_do_declarante = self.natureza_declarante
        dirf.cpf_responsavel = ''
        dirf.data_do_evento_decpj = ''
        print(dirf.DECPJ)

        # Identificação do Código da receita - IDREC
        dirf.codigo_da_receita = '0651'
        print(dirf.IDREC)

        # Preencher beneficiarios
        for contract_id in self.contract_ids:
            beneficiario = Beneficiario()
            beneficiario.cpf_bpfdec = contract_id.employee_id.cpf
            beneficiario.nome_bpfdec = contract_id.employee_id.name
            self.populate_beneficiario(beneficiario, contract_id, self.ano)
            dirf.add_beneficiario(beneficiario)

        print(dirf.BPFDEC)

# -*- coding: utf-8 -*-
# (c) 2019 Hendrix Costa <hendrix.costa@abgf.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from __future__ import (
    division, print_function, unicode_literals, absolute_import
)

from openerp import api, fields, models
from openerp.exceptions import Warning

from .arquivo_dirf import DIRF, Beneficiario

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
        string=u'Prévia do SEFIP',
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

                record.contract_ids = self.env['hr.contract'].search(domain)

    @api.multi
    def buscar_holerites(self, contract_id, ano):
        """
        """
        for record in self:
            domain = [
                ('contract_id', '=', contract_id.id),
                ('ano', '=', int(ano)),
                ('tipo_de_folha','in', ['normal','decimo_terceiro']),
                ('is_simulacao', '=', False),
                ('state', 'in', ['done', 'verify']),
            ]
            return self.env['hr.payslip'].search(domain)


    @api.multi
    def get_valor_bruto_mes(self, holerites_ids, mes, tipo='normal'):
        """
        """
        holerites_ids = \
            holerites_ids.filtered(lambda x: x.tipo_de_folha == tipo)
        if tipo == 'decimo_terceiro':
            total = sum(holerites_ids.mapped('line_ids').
                        filtered(lambda x: x.code == 'BRUTO').mapped('total'))
        else:
            holerite_id = holerites_ids.filtered(lambda x: x.mes_do_ano2 == mes)
            if len(holerite_id) > 1:
                raise Warning(
                    'Mais de 1 Holerite encontrado para o mesmo Funcionário'
                    ' no mesmo período.\n{} - {}/{}'.format(
                    holerite_id[0].employee_id.name, mes, self.ano))
            line_id = holerite_id.line_ids.filtered(lambda x: x.code == 'BRUTO')
            total = line_id.total

        return total

    @api.multi
    def populate_beneficiario(self, beneficiario, contract_id, ano):
        for record in self:
            holerites_ids = self.buscar_holerites(contract_id, ano)
            beneficiario.janeiro = self.get_valor_bruto_mes(holerites_ids, 1)
            beneficiario.fevereiro = self.get_valor_bruto_mes(holerites_ids, 2)
            beneficiario.marco = self.get_valor_bruto_mes(holerites_ids, 3)
            beneficiario.abril = self.get_valor_bruto_mes(holerites_ids, 4)
            beneficiario.maio = self.get_valor_bruto_mes(holerites_ids, 5)
            beneficiario.junho = self.get_valor_bruto_mes(holerites_ids, 6)
            beneficiario.julho = self.get_valor_bruto_mes(holerites_ids, 7)
            beneficiario.agosto = self.get_valor_bruto_mes(holerites_ids, 8)
            beneficiario.setembro = self.get_valor_bruto_mes(holerites_ids, 9)
            beneficiario.outubro = self.get_valor_bruto_mes(holerites_ids, 10)
            beneficiario.novembro = self.get_valor_bruto_mes(holerites_ids, 11)
            beneficiario.dezembro = self.get_valor_bruto_mes(holerites_ids, 12)
            beneficiario.decimo_terceiro = self.get_valor_bruto_mes(
                holerites_ids, 13, tipo='decimo_terceiro')

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

        # Organizar contratos
        sorted_contract_ids = \
            self.contract_ids[:8].sorted(key=lambda x: x.employee_id.cpf)

        for contract_id in sorted_contract_ids:
            beneficiario = Beneficiario()
            beneficiario.cpf_bpfdec = contract_id.employee_id.cpf
            beneficiario.nome_bpfdec = contract_id.employee_id.name

            self.populate_beneficiario(beneficiario, contract_id, self.ano)

            dirf.add_beneficiario_PF(beneficiario)

        print(dirf.BPFDEC)

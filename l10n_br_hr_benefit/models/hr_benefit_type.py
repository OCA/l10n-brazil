# -*- coding: utf-8 -*-
# Copyright 2019 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from __future__ import (absolute_import, division,
                        print_function, unicode_literals)

from openerp import api, fields, models, _
from openerp.exceptions import Warning

ADMISSION_SELECTION = [
    ('full', 'Integral'),
    ('partial', 'Parcial'),
    ('rule15days', 'Regra dos 15 dias'),
    ('rulexdays', 'Mínimo de dias trabalhados'),
]


class HrBenefitType(models.Model):
    _name = b'hr.benefit.type'
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _description = 'Tipo de Benefício'
    _order = 'name, date_start desc, date_stop desc'

    name = fields.Char(
        string='Tipo',
        required=True,
        index=True,
    )
    date_start = fields.Date(
        string='Data Início',
        index=True,
        track_visibility='onchange',
        help='Data de início da vigência deste tipo de benefício.',
    )
    date_stop = fields.Date(
        string='Data Fim',
        index=True,
        track_visibility='onchange',
        help='Data de fim da vigência deste tipo de benefício.',
    )
    amount_max = fields.Float(
        string='Valor máximo',
        index=True,
        track_visibility='onchange'
    )
    amount = fields.Float(
        string='Valor',
        index=True,
        track_visibility='onchange'
    )
    percent = fields.Float(
        string='(%) do valor',
        index=True,
        track_visibility='onchange'
    )
    need_approval = fields.Boolean(
        string='Aprovação gerencial',
        track_visibility='onchange',
        help='Adiciona necessidade de aprovação gerencial para criação de um '
             'benefício deste tipo',
    )
    need_approval_file = fields.Boolean(
        string='Anexo obrigatório',
        track_visibility='onchange',
        help='Adiciona necessidade de arquivo de anexo para criação de um '
             'benefício deste tipo',
    )
    line_need_approval = fields.Boolean(
        string='Aprovação gerencial',
        track_visibility='onchange',
        help='Adiciona necessidade de aprovação gerencial para aprovar as '
             'prestações de contas deste benefício',
    )
    line_need_approval_file = fields.Boolean(
        string='Anexo obrigatório',
        track_visibility='onchange',
        help='Adiciona necessidade de documento anexo para aprovar as '
             'prestações de contas deste benefício',
    )
    line_days_approval_limit = fields.Integer(
        string='Limite de aprovação em dias',
        help='Limite em dias para aprovar o benefício. Após esse limite '
             'somente um funcionário do RH poderá aprová-lo.',
    )
    income_rule_id = fields.Many2one(
        comodel_name="hr.salary.rule",
        # required=True,
        string=u"Provento / Benefício (+)",
        help='Rúbrica de provento utilizada pelo benefício',
    )
    deduction_rule_id = fields.Many2one(
        comodel_name="hr.salary.rule",
        # required=True,
        string=u"Dedução / Desconto (-)",
        help='Rúbrica de dedução utilizada pelo benefício',
    )
    python_code = fields.Text(
        string='Código Python',
        track_visibility='onchange'
    )
    contract_category_ids = fields.Many2many(
        comodel_name='hr.contract.category',
        string='Categorias de Contratos',
        ondelete='restrict',
    )
    type_calc = fields.Selection(
        selection=[
            ('fixed', 'Valor Fixo'),
            ('daily', 'Valor Diário'),
            ('max', 'Limitado ao teto'),
            ('percent', '% do valor gasto'),
            ('percent_max', '% do valor gasto, limitado ao teto'),
        ],
        string='Tipo de Cálculo',
        required=True,
        help='Cálculo utilizado para o valor final do benefício',
    )
    min_worked_days = fields.Integer(
        default=0,
        string='Mín dias trabalhados',
        track_visibility='onchange'
    )
    line_need_clearance = fields.Boolean(
        string='Necessita Apuração?',
        default=True,
        track_visibility='onchange',
        help='O funcionário precisará inserir valor e clicar em apurar caso '
             'selecionado.',
    )
    line_group_benefits = fields.Boolean(
        string='Agrupar prestação de contas?',
        default=True,
        track_visibility='onchange',
        help='Caso selecionado, múltiplos benefícios serão inseridos numa '
             'única entrada de holerite.',
    )
    daily_admission_type = fields.Selection(
        string='Benefício na Admissão',
        selection=ADMISSION_SELECTION,
        default='partial',
    )
    beneficiary_list = fields.Boolean(
        string="Usar lista de beneficiarios ao invés de parceiro",
        help='Utiliza uma lista de nomes de beneficiários ao invés de '
             'selecionar um parceiro para receber este benefício. Usado no '
             'benefício seguro de vida.',
    )
    extra_income = fields.Boolean(
        string='13º Benefício?',
        default=False,
        help='Caso selecionado, o benefício será aplicado, também, no mês do '
             '13º salário.',
    )
    extra_income_month = fields.Selection(
        string='Mês 13º Benefício',
        selection=[
            ('1', 'Janeiro'),
            ('2', 'Fevereiro'),
            ('3', 'Março'),
            ('4', 'Abril'),
            ('5', 'Maio'),
            ('6', 'Junho'),
            ('7', 'Julho'),
            ('8', 'Agosto'),
            ('9', 'Setembro'),
            ('10', 'Outubro'),
            ('11', 'Novembro'),
            ('12', 'Dezembro')
        ],
    )

    @api.onchange('extra_income')
    def _onchange_extra_income(self):
        if not self.extra_income:
            self.extra_income_month = False

    @api.onchange('line_need_approval', 'line_need_approval_file')
    def _onchange_line_need_clearance(self):
        if self.line_need_approval or self.line_need_approval_file:
            self.line_need_clearance = True

    @api.one
    @api.constrains("date_start", "date_stop", "name")
    def _check_dates(self):
        overlap = self.search(
            [
                ('id', '!=', self.id),
                ('name', '=', self.name),
                ('date_start', '<=', self.date_start),
                '|',
                ('date_stop', '=', False),
                ('date_stop', '>=', self.date_start),
            ]
        )
        if overlap:
            raise Warning(
                _('Já existe um tipo de benefício '
                  'com o mesmo nome e com datas'
                  ' que sobrepõem essa'))

    @api.multi
    def name_get(self):
        result = []
        for record in self:
            name = "%s" % record.name
            if record.date_start and not record.date_stop:
                name += ' (a partir de %s)' % record.date_start
            elif record.date_start and record.date_stop:
                name += ' (de %s até %s)' % (
                    record.date_start, record.date_stop)

            result.append((record['id'], name))
        return result

    @api.model
    def create(self, vals):
        hr_users = self.env.ref('base.group_hr_user').users
        partner_ids = [user.partner_id.id for user in hr_users]
        vals.update({
            'message_follower_ids': partner_ids
        })
        return super(HrBenefitType, self).create(vals)

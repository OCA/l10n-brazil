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
        string='Date Start',
        index=True,
        track_visibility='onchange'
    )
    date_stop = fields.Date(
        string='Date Stop',
        index=True,
        track_visibility='onchange'
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
        track_visibility='onchange'
    )
    need_approval_file = fields.Boolean(
        string='Anexo obrigatório',
        track_visibility='onchange'
    )
    line_need_approval = fields.Boolean(
        string='Aprovação gerencial',
        track_visibility='onchange'
    )
    line_need_approval_file = fields.Boolean(
        string='Anexo obrigatório',
        track_visibility='onchange'
    )
    line_days_approval_limit = fields.Integer(
        string='Limite de aprovação em dias'
    )
    income_rule_id = fields.Many2one(
        comodel_name="hr.salary.rule",
        # required=True,
        string=u"Provento / Benefício (+)",
    )
    deduction_rule_id = fields.Many2one(
        comodel_name="hr.salary.rule",
        # required=True,
        string=u"Dedução / Desconto (-)",
    )
    python_code = fields.Text(
        string='Código Python',
        track_visibility='onchange'
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
    )
    line_group_benefits = fields.Boolean(
        string='Agrupar prestação de contas?',
        default=True,
        track_visibility='onchange',
    )
    daily_admission_type = fields.Selection(
        string='Benefício na Admissão',
        selection=ADMISSION_SELECTION,
        default='partial',
    )
    beneficiary_list = fields.Boolean(
        string="Usar lista de beneficiarios ao invés de parceiro"
    )
    extra_income = fields.Boolean(
        string='13º Cesta?',
        default=False,
    )
    extra_income_month = fields.Selection(
        string='Mês 13º Cesta',
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
    instrucao = fields.Html(
        string='Instrução para Importação',
        compute='_get_default_instrucao',
        readonly=True,
    )

    def _get_default_instrucao(self):
        self.instrucao = """
        
        <br />
        <h3>Variáveis disponíveis</h3> 
        <br />
        
        <style type="text/css">
.tg  {border-collapse:collapse;border-spacing:0;border-color:#aabcfe;}
.tg td{font-family:Arial, sans-serif;font-size:14px;padding:10px 5px;border-style:solid;border-width:1px;overflow:hidden;word-break:normal;border-color:#aabcfe;color:#669;background-color:#e8edff;}
.tg th{font-family:Arial, sans-serif;font-size:14px;font-weight:normal;padding:10px 5px;border-style:solid;border-width:1px;overflow:hidden;word-break:normal;border-color:#aabcfe;color:#039;background-color:#b9c9fe;}
.tg .tg-phtq{background-color:#D2E4FC;border-color:inherit;text-align:left;vertical-align:top}
.tg .tg-baqh{text-align:center;vertical-align:top}
.tg .tg-c3ow{border-color:inherit;text-align:center;vertical-align:top}
.tg .tg-0pky{border-color:inherit;text-align:left;vertical-align:top}
.tg .tg-svo0{background-color:#D2E4FC;border-color:inherit;text-align:center;vertical-align:top}
.tg .tg-0lax{text-align:left;vertical-align:top}
</style>

<ul class="tg" class="oe_center">
    <li><b>
        amount_benefit
    </b></li>
    <ul><li>
        Valor Apurado
    </li></ul>
    
    <li><b>
        amount_base
    </b></li>
    <ul><li>
        Valor Comprovado
    </li></ul>
    
    <li><b>
        income_amount
    </b></li>
    <ul><li>
        Valor apurado do Provento
    </li></ul>
    
    <li><b>
        income_percentual
    </b></li>
    <ul><li>
        Percentual apurado do Provento
    </li></ul>
    
    <li><b>
        income_quantity
    </b></li>
    <ul><li>
        Quantidade apurada do Provento
    </li></ul>
    
    <li><b>
        deduction_amount
    </b></li>
    <ul><li>
        Valor apurado da Dedução
    </li></ul>
    
    <li><b>
        deduction_percentual
    </b></li>
    <ul><li>
        Percentual apurado da Dedução
    </li></ul>
    
    <li><b>
        deduction_quantity
    </b></li>
    <ul><li>
        Quantidadae apurada da Dedução
    </li></ul>
    
    <li><b>
        max_age_full_income
    </b></li>
    <ul><li>
        Idade máxima, em meses, para receber o auxílio Creche/Babá em sua totalidade. O valor apurado é, neste caso, igual ao valor comprovado. (Caso não preenchido, o valor padrão é 5 meses)
    </li></ul>
    
    <li><b>
        max_age_income
    </b></li>
    <ul><li>
        Idade máxima, em meses, para receber o auxílio Creche/Babá até o limite do teto. O valor apurado é, neste caso, o menor valor entre teto e valor comprovado. (Caso não preenchido, o valor padrão é 71 meses)
    </li></ul>
</ul>
        """

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

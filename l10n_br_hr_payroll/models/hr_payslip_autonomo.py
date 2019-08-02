# -*- coding: utf-8 -*-
# Copyright (C) 2018 ABGF (http://www.abgf.gov.br)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import logging
from datetime import datetime

from dateutil.relativedelta import relativedelta
from lxml import etree
from openerp import api, fields, models, exceptions, _

_logger = logging.getLogger(__name__)

try:
    from pybrasil import valor, data
    from pybrasil.data import ultimo_dia_mes
    from pybrasil.valor.decimal import Decimal

except ImportError:
    _logger.info('Cannot import pybrasil')

MES_DO_ANO = [
    (1, u'Janeiro'),
    (2, u'Fevereiro'),
    (3, u'Março'),
    (4, u'Abril'),
    (5, u'Maio'),
    (6, u'Junho'),
    (7, u'Julho'),
    (8, u'Agosto'),
    (9, u'Setembro'),
    (10, u'Outubro'),
    (11, u'Novembro'),
    (12, u'Dezembro'),
]

TIPO_DE_FOLHA = [
    ('normal', u'Folha normal'),
    ('rpa', u'Recibo de Pagamento a Autonômo'),
    ('rescisao', u'Rescisão'),
    ('ferias', u'Férias'),
    ('decimo_terceiro', u'Décimo terceiro (13º)'),
    ('aviso_previo', u'Aviso Prévio'),
    ('provisao_ferias', u'Provisão de Férias'),
    ('provisao_decimo_terceiro', u'Provisão de Décimo terceiro (13º)'),
    ('licenca_maternidade', u'Licença maternidade'),
    ('auxilio_doenca', u'Auxílio doença'),
    ('auxílio_acidente_trabalho', u'Auxílio acidente de trabalho'),
]


class HrPayslipAutonomo(models.Model):
    _name = 'hr.payslip.autonomo'
    _order = 'ano desc, mes_do_ano desc, company_id asc, employee_id asc'

    name = fields.Char(
        string='name',
        compute='_compute_name'
    )

    contract_id = fields.Many2one(
        comodel_name = 'hr.contract',
        string= 'Contrato',
        ondelete='cascade',
        index=True,
    )

    employee_id = fields.Many2one(
        string=u'Funcionário',
        comodel_name='hr.employee',
        compute='_compute_set_employee_id',
        store=True,
        required=False,
        states={'draft': [('readonly', False)]}
    )

    state = fields.Selection(
        selection = [
            ('draft', 'Draft'),
            ('verify', 'Waiting'),
            ('done', 'Done'),
            ('cancel', 'Rejected'),
        ],
        default='draft',
        string='Status',
        copy=False,
    )

    mes_do_ano = fields.Selection(
        selection=MES_DO_ANO,
        string=u'Mês',
        compute='_compute_mes_ano_contrato',
        store=True,
    )

    ano = fields.Integer(
        string=u'Ano',
        compute='_compute_mes_ano_contrato',
        store=True,
    )

    date_from = fields.Date(
        string='Date From',
        compute='_compute_contract_date',
        store=True,
    )

    date_to = fields.Date(
        string='Date To',
        compute='_compute_contract_date',
        store=True,
    )

    struct_id = fields.Many2one(
        string=u'Estrutura de Salário',
        comodel_name='hr.payroll.structure',
        compute='_compute_struct_id',
        store=True,
        states={'draft': [('readonly', False)]},
        help=u'Defines the rules that have to be applied to this payslip, '
             u'accordingly to the contract chosen. If you let empty the field '
             u'contract, this field isn\'t mandatory anymore and thus the '
             u'rules applied will be all the rules set on the structure of all'
             u' contracts of the employee valid for the chosen period'
    )

    line_ids = fields.One2many(
        string=u"Holerite Resumo",
        comodel_name='hr.payslip.line',
        inverse_name='slip_autonomo_id',
    )

    line_resume_ids = fields.One2many(
        comodel_name='hr.payslip.line',
        inverse_name='slip_autonomo_id',
        compute='_buscar_payslip_line',
        string=u"Holerite Resumo",
    )

    is_simulacao = fields.Boolean(
        string=u"Simulação",
    )

    tipo_de_folha = fields.Selection(
        selection=TIPO_DE_FOLHA,
        string=u'Tipo de folha',
        default='normal',
    )

    data_mes_ano = fields.Char(
        string=u'Mês/Ano',
        compute='_compute_data_mes_ano',
    )

    total_folha = fields.Float(
        string=u'Total',
        default=0.00,
        compute='_compute_valor_total_folha'
    )

    total_folha_fmt = fields.Char(
        string=u'Total',
        default='0',
        compute='_compute_valor_total_folha'
    )

    salario_base_fmt = fields.Char(
        string=u'Salario Base',
        default='0',
        compute='_compute_valor_total_folha'
    )

    data_extenso = fields.Char(
        string=u'Data por Extenso',
        compute='_compute_valor_total_folha'
    )

    company_id = fields.Many2one(
        string="Empresa",
        comodel_name="res.company",
        related='contract_id.company_id',
        store=True
    )

    total_proventos = fields.Float(
        string=u'Total Proventos',
        default=0.00,
        compute='_compute_valor_total_folha'
    )

    total_proventos_fmt = fields.Char(
        string=u'Total Proventos',
        default='0',
        compute='_compute_valor_total_folha'
    )

    total_descontos = fields.Float(
        string=u'Total Descontos',
        default=0.00,
        compute='_compute_valor_total_folha'
    )

    total_descontos_fmt = fields.Char(
        string=u'Total Descontos',
        default='0',
        compute='_compute_valor_total_folha'
    )

    data_pagamento_autonomo = fields.Date(
        string=u'Data de Pagamento',
        default=fields.Date.context_today,
    )

    number = fields.Char(
        string='Reference',
        readonly=True,
        states={'draft': [('readonly', False)]},
        copy=False
    )

    @api.multi
    @api.depends('contract_id')
    def _compute_mes_ano_contrato(self):
        for record in self:
            if record.contract_id:
                data = record.contract_id.date_start.split('-')
                record.mes_do_ano = int(data[1])
                record.ano = int(data[0])

    @api.multi
    @api.depends('contract_id')
    def _compute_contract_date(self):
        for record in self:
            if record.contract_id:
                record.date_from = record.contract_id.date_start
                record.date_to = record.contract_id.date_end

    @api.multi
    @api.depends('mes_do_ano', 'ano', 'contract_id')
    def _compute_name(self):
        """
         Definir nome do RPA
        """
        for record in self:
            name = 'Recibo de pagamento - {}'.format(
                record.contract_id.display_name)
            if record.mes_do_ano and record.ano:
                name += str(record.mes_do_ano) + '/' + str(record.ano)
            record.name = name

    @api.multi
    def _compute_valor_total_folha(self):
        for holerite in self:
            total = 0.00
            total_proventos = 0.00
            total_descontos = 0.00
            base_inss = 0.00
            base_irpf = 0.00
            base_fgts = 0.00
            fgts = 0.00
            inss = 0.00
            irpf = 0.00
            #            codigo = {}
            #            codigo['BASE_FGTS'] = \
            #                holerite.env\
            #                .ref('l10n_br_hr_payroll.hr_salary_rule_BASE_FGTS').code
            #            codigo['BASE_INSS'] = \
            #                holerite.env\
            #                .ref('l10n_br_hr_payroll.hr_salary_rule_BASE_INSS').code
            #            codigo['BASE_IRPF'] = \
            #                holerite.env\
            #                .ref('l10n_br_hr_payroll.hr_salary_rule_BASE_IRPF').code
            #            codigo['FGTS'] = \
            #                holerite.env\
            #                .ref('l10n_br_hr_payroll.hr_salary_rule_FGTS').code
            #            codigo['INSS'] = \
            #                holerite.env\
            #                .ref('l10n_br_hr_payroll.hr_salary_rule_INSS').code
            #            codigo['IRPF'] = \
            #                holerite.env\
            #                .ref('l10n_br_hr_payroll.hr_salary_rule_IRPF').code
            for line in holerite.line_ids:
                total += line.valor_provento - line.valor_deducao
                total_proventos += line.valor_provento
                total_descontos += line.valor_deducao
                if line.code in ['BASE_FGTS', 'BASE_FGTS_13']:
                    base_fgts += line.total
                elif line.code in ['BASE_INSS', 'BASE_INSS_13']:
                    base_inss += line.total
                elif line.code == 'BASE_IRPF':
                    base_irpf = line.total
                elif line.code == 'FGTS':
                    fgts = line.total
                elif line.code == 'INSS':
                    inss = line.total
                elif line.code == 'IRPF':
                    irpf = line.total
            holerite.total_folha = total
            holerite.total_proventos = total_proventos
            holerite.total_descontos = total_descontos
            holerite.base_fgts = base_fgts
            holerite.base_inss = base_inss
            holerite.base_irpf = base_irpf
            holerite.fgts = fgts
            holerite.inss = inss
            holerite.irpf = irpf
            # Formato
            holerite.data_admissao_fmt = \
                data.formata_data(holerite.contract_id.date_start)
            holerite.salario_base_fmt = \
                valor.formata_valor(holerite.contract_id.wage)
            holerite.total_folha_fmt = \
                valor.formata_valor(holerite.total_folha)
            holerite.total_proventos_fmt = \
                valor.formata_valor(holerite.total_proventos)
            holerite.total_descontos_fmt = \
                valor.formata_valor(holerite.total_descontos)
            holerite.base_fgts_fmt = valor.formata_valor(holerite.base_fgts)
            holerite.base_inss_fmt = valor.formata_valor(holerite.base_inss)
            holerite.base_irpf_fmt = valor.formata_valor(holerite.base_irpf)
            holerite.fgts_fmt = valor.formata_valor(holerite.fgts)
            holerite.inss_fmt = valor.formata_valor(holerite.inss)
            holerite.irpf_fmt = valor.formata_valor(holerite.irpf)
            holerite.data_extenso = data.data_por_extenso(fields.Date.today())
            # holerite.data_retorno = data.formata_data(
            #     str((fields.Datetime.from_string(holerite.date_to) +
            #          relativedelta(days=1)).date()))

            # holerite.data_pagamento = str(
            #     self.compute_payment_day(holerite.date_from))

            # TO DO Verificar datas de feriados.
            # A biblioteca aceita os parametros de feriados, mas a utilizacao
            # dos feriados é diferente do odoo.
            # Logo o método só é utilizado para antecipar em casos de finais
            # de semana.
            # holerite.data_pagamento = data.formata_data(
            #     data.dia_util_pagamento(
            #         data_vencimento=holerite.data_pagamento, antecipa=True,
            #     )
            # )

    #
    #  Métodos da payslip do autonomo
    #
    @api.multi
    @api.onchange('contract_id')
    def _onchange_contract_id(self):
        for record in self:
            if record.contract_id:
                primeiro_dia_do_mes = str(
                    datetime.strptime(str(record.mes_do_ano) + '-' +
                                      str(record.ano), '%m-%Y').date())

                record.date_from = \
                    max(primeiro_dia_do_mes, record.contract_id.date_start)

                ultimo_dia_do_mes = str(
                    self.env['resource.calendar'].get_ultimo_dia_mes(
                        record.mes_do_ano, record.ano).date())

                record.date_to = \
                    min(record.contract_id.date_end, ultimo_dia_do_mes)

    @api.multi
    def _compute_data_mes_ano(self):
        for record in self:
            record.data_mes_ano = MES_DO_ANO[record.mes_do_ano - 1][1][:3] + \
                '/' + str(record.ano)

    @api.multi
    def button_hr_validate_payslip_autonomo(self):
        """
        Validar Holerite Calculado. Estado vai para Done
        """
        for record in self:
            record.state = 'done'
            record.number = self.env['ir.sequence'].get('salary.slip')

    @api.multi
    @api.depends('line_ids')
    def _buscar_payslip_line(self):
        for holerite in self:
            lines = []
            for line in holerite.line_ids:
                if line.valor_provento or line.valor_deducao:
                    lines.append(line.id)
            holerite.line_resume_ids = lines

    @api.multi
    def compute_sheet_autonomo(self):
        """
        """
        for holerite in self:
            # delete old payslip lines
            holerite.line_ids.unlink()

            # Gerar Linhas do Holerite
            lines = [(0, 0, line) for line in self.get_payslip_lines()]
            holerite.write({'line_ids': lines})

            # Gerar Resumo do Holerite
            holerite._buscar_payslip_line()

        return True

    def cancel_sheet(self):
        return self.write({'state': 'cancel'})

    @api.multi
    def unlink(self):
        for payslip in self:
            if payslip.state not in ['draft', 'cancel']:
                raise exceptions.Warning(
                    _('You cannot delete a payslip which is not '
                      'draft or cancelled or permission!')
                )
            payslip.cancel_sheet()
        return super(HrPayslipAutonomo, self).unlink()

    @api.multi
    @api.depends('contract_id', 'mes_do_ano')
    def _compute_set_employee_id(self):
        for record in self:
            if record.contract_id:
                record.employee_id = record.contract_id.employee_id

    @api.multi
    @api.depends('contract_id', 'mes_do_ano')
    def _compute_struct_id(self):
        """
        Definir a estrutura que processara o holerite do autonomo
        """
        for record in self:
            if record.contract_id:
                record.struct_id = record.contract_id.struct_id

    @api.multi
    def get_payslip_lines(self):
        """
        """

        def _sum_salary_rule_category(localdict, category, amount):
            if category.parent_id:
                localdict = _sum_salary_rule_category(
                    localdict, category.parent_id, amount)
            localdict['categories'].dict[category.code] = \
                category.code in localdict['categories'].dict and \
                localdict['categories'].dict[category.code] + amount or amount
            return localdict

        class BrowsableObject(object):
            def __init__(self, employee_id, dict):
                self.employee_id = employee_id
                self.dict = dict

            def __getattr__(self, attr):
                return attr in self.dict and self.dict.__getitem__(attr) or 0.0

        # we keep a dict with the result because a value can be overwritten
        # by another rule with the same code
        result_dict = {}
        rules = {}
        categories_dict = {}
        blacklist = []
        payslip_obj = self.env['hr.payslip']
        obj_rule = self.env['hr.salary.rule']
        medias = {}
        categories_obj = BrowsableObject(self.employee_id.id, categories_dict)

        # Variaveis para INSS patronal
        rat_fap = self._get_rat_fap_period_values(self.ano)

        baselocaldict = {
            'CALCULAR': self,
            'BASE_INSS': 0.0, 'BASE_FGTS': 0.0, 'BASE_IR': 0.0,
            'categories': categories_obj,
            'locals': locals, 'globals': locals,
            'Decimal': Decimal, 'D': Decimal,
            'payslip': self,
            'RAT_FAP': rat_fap,
        }

        for contract_id in self.contract_id:
            # recuperar todas as estrututras que serao processadas
            # (estruturas da payslip atual e as estruturas pai da payslip)
            structure_ids = self.struct_id._get_parent_structure()

            # recuperar as regras das estruturas e filha de cada regra
            rule_ids = self.env['hr.payroll.structure'].browse(
                structure_ids).get_all_rules()

            # Caso nao esteja computando holerite de provisão de ferias ou
            # de decimo terceiro recuperar as regras especificas do contrato
            applied_specific_rule = \
                self.get_contract_specific_rubrics(contract_id, rule_ids)

            # organizando as regras pela sequencia de execução definida
            sorted_rule_ids = \
                [id for id, sequence in sorted(rule_ids, key=lambda x: x[1])]

            employee = contract_id.employee_id
            localdict = \
                dict(baselocaldict, employee=employee, contract=contract_id)

            for rule in obj_rule.browse(sorted_rule_ids):
                key = rule.code + '-' + str(self.id)
                localdict['result'] = None
                localdict['result_qty'] = 1.0
                localdict['result_rate'] = 100
                localdict['rubrica'] = rule
                id_rubrica_especifica = 0
                beneficiario_id = False

                # check if the rule can be applied
                if obj_rule.satisfy_condition(rule.id, localdict) \
                        and rule.id not in blacklist:
                    # compute the amount of the rule
                    amount, qty, rate = \
                        obj_rule.compute_rule(rule.id, localdict)

                    # se ja tiver sido calculado a media dessa rubrica,
                    # utilizar valor da media e multiplicar
                    # pela reinciden.
                    if medias.get(rule.code):
                        amount = medias.get(rule.code).media / 12
                        qty = medias.get(rule.code).meses
                        rule.name += ' (Media) '

                    # check if there is already a rule computed
                    # with that code
                    previous_amount = \
                        rule.code in localdict and \
                        localdict[rule.code] or 0.0
                    # previous_amount = 0
                    # set/overwrite the amount computed
                    # for this rule in the localdict
                    tot_rule = Decimal(amount or 0) * Decimal(
                        qty or 0) * Decimal(rate or 0) / 100.0
                    tot_rule = tot_rule.quantize(Decimal('0.01'))
                    localdict[rule.code] = tot_rule
                    rules[rule.code] = rule

                    # Adiciona a rubrica especifica ao localdict
                    if id_rubrica_especifica:
                        localdict['RUBRICAS_ESPEC_CALCULADAS'].append(
                            id_rubrica_especifica)

                    # sum the amount for its salary category
                    localdict = _sum_salary_rule_category(
                        localdict, rule.category_id,
                        tot_rule - previous_amount)

                    # Definir o partner que recebera o pagamento da linha
                    if not beneficiario_id and \
                            contract_id.employee_id.address_home_id:
                        beneficiario_id = \
                            contract_id.employee_id.address_home_id.id

                    # create/overwrite the rule in the temporary results
                    result_dict[key] = {
                        'salary_rule_id': rule.id,
                        'contract_id': contract_id.id,
                        'name': rule.name,
                        'code': rule.code,
                        'category_id': rule.category_id.id,
                        'sequence': rule.sequence,
                        'appears_on_payslip': rule.appears_on_payslip,
                        'condition_select': rule.condition_select,
                        'condition_python': rule.condition_python,
                        'condition_range': rule.condition_range,
                        'condition_range_min':
                            rule.condition_range_min,
                        'condition_range_max':
                            rule.condition_range_max,
                        'amount_select': rule.amount_select,
                        'amount_fix': rule.amount_fix,
                        'amount_python_compute':
                            rule.amount_python_compute,
                        'amount_percentage': rule.amount_percentage,
                        'amount_percentage_base':
                            rule.amount_percentage_base,
                        'register_id': rule.register_id.id,
                        'amount': amount,
                        'employee_id': contract_id.employee_id.id,
                        'quantity': qty,
                        'rate': rate,
                        'partner_id': beneficiario_id or 1,
                    }

                    blacklist.append(rule.id)
                else:
                    rules_seq = rule._model._recursive_search_of_rules(
                        self._cr, self._uid, rule, self._context)
                    blacklist += [id for id, seq in rules_seq]
                    continue

                if rule.category_id.code == 'DEDUCAO':
                    if rule.compoe_base_INSS:
                        localdict['BASE_INSS'] -= tot_rule
                    if rule.compoe_base_IR:
                        localdict['BASE_IR'] -= tot_rule
                    if rule.compoe_base_FGTS:
                        localdict['BASE_FGTS'] -= tot_rule
                else:
                    if rule.compoe_base_INSS:
                        localdict['BASE_INSS'] += tot_rule
                    if rule.compoe_base_IR:
                        localdict['BASE_IR'] += tot_rule
                    if rule.compoe_base_FGTS:
                        localdict['BASE_FGTS'] += tot_rule

            result = [value for code, value in result_dict.items()]
            return result

    @api.model
    def fields_view_get(self, view_id=None, view_type='form',
                        toolbar=False, submenu=False):
        res = super(HrPayslipAutonomo, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar,
            submenu=submenu)

        if view_type == 'form':
            doc = etree.XML(res['arch'])
            for sheet in doc.xpath("//sheet"):
                parent = sheet.getparent()
                index = parent.index(sheet)
                for child in sheet:
                    parent.insert(index, child)
                    index += 1
                parent.remove(sheet)
            res['arch'] = etree.tostring(doc)
        return res

    @api.multi
    def get_contract_specific_rubrics(self, rule_ids):
        self.ensure_one()
        applied_specific_rule = {}
        for specific_rule in self.contract_id.specific_rule_ids:
            if self.date_from >= specific_rule.date_start:
                if not specific_rule.date_stop or \
                        self.date_to <= specific_rule.date_stop:

                    rule_ids.append((specific_rule.rule_id.id,
                                     specific_rule.rule_id.sequence))

                    if specific_rule.rule_id.id not in applied_specific_rule:
                        applied_specific_rule[specific_rule.rule_id.id] = []

                    applied_specific_rule[specific_rule.rule_id.id].append(
                        specific_rule)

        return applied_specific_rule

    def INSS(self, BASE_INSS):
        """
        Cálculo do INSS da folha de pagamento. Essa função é responsável por
        disparar o cálculo do INSS, que fica embutido em sua classe.
         Essa função está dísponivel no context das rubricas sendo possível
         inserir o seguinte código python na rubrica:
         result = CALCULAR.INSS(<variavel que contem a base do INSS>)
         *CALCULAR é a instancia corrente da payslip
        :param BASE_INSS: - float - soma das rubricas que compoe o INSS
        :return: float - Valor do inss a ser descontado do funcionario
        """
        tabela_inss_obj = self.env['l10n_br.hr.social.security.tax']
        if BASE_INSS:
            inss = tabela_inss_obj._compute_inss(BASE_INSS, self.date_from)
            return inss
        else:
            return 0

    def BASE_IRRF(self, TOTAL_IRRF, INSS):
        """
        Calcula a base de cálculo do IRRF. A formula se da por:
        BASE_IRRF = BASE_INSS - INSS -
            (DESCONTO_POR_DEPENDENTE * QTY_DE_DEPENDENTES)

        :param TOTAL_IRRF:  - float - Soma das rubricas que compoem a BASE_IRRF
        :param INSS:        - float - Valor do INSS a ser descontado
                                      do funcionario
        :return:            - float - base do IRRF
        """
        ano = fields.Datetime.from_string(self.date_from).year

        deducao_dependente_obj = self.env[
            'l10n_br.hr.income.tax.deductable.amount.family'
        ]
        deducao_dependente_value = deducao_dependente_obj.search(
            [('year', '=', ano)], order='create_date DESC', limit=1
        )
        dependent_values = 0
        for dependente in self.employee_id.dependent_ids:
            if dependente.dependent_verification and \
                    dependente.dependent_dob < self.date_from:
                dependent_values += deducao_dependente_value.amount

        return TOTAL_IRRF - INSS - dependent_values

    def IRRF(self, BASE_IRRF, INSS):
        tabela_irrf_obj = self.env['l10n_br.hr.income.tax']
        if BASE_IRRF:
            irrf = tabela_irrf_obj._compute_irrf(
                BASE_IRRF, self.employee_id.id, INSS, self.date_from
            )
            return irrf
        else:
            return 0

    @api.multi
    def _get_rat_fap_period_values(self, year):
        rat_fap_obj = self.env['l10n_br.hr.rat.fap']
        rat_fap = rat_fap_obj = rat_fap_obj.search(
            [('year', '=', year), ('company_id', '=', self.company_id.id)]
        )
        if rat_fap:
            return rat_fap
        else:
            raise exceptions.Warning(
                _('Can\'t find this year values in Rat Fap Table')
            )

    def get_specific_rubric_value(self, rubrica_id, medias_obj=False,
                                  rubricas_especificas_calculadas=False):
        """
        Função dísponivel para as regras de salario, que busca o valor das
        rubricas especificas cadastradas no contrato.
        :param rubrica_id: int - id da regra de salario corrente
        :param medias_obj: ?
        :param rubricas_spec_calculadas - lista dos ids das rubricas
                                        especificas que ja foram computadas
        :return: valor da rubrica especifica cadastrado no contrato ou 0.
        """
        for rubrica in self.contract_id.specific_rule_ids:
            # Se a rubrica_especifica ja tiver sido calculada segue pra próxima
            if rubricas_especificas_calculadas and \
                    rubrica.id in rubricas_especificas_calculadas:
                continue
            if rubrica.rule_id.id == rubrica_id \
                    and rubrica.date_start <= self.date_from and \
                    (not rubrica.date_stop or rubrica.date_stop >=
                        self.date_to):
                if medias_obj:
                    if rubrica.rule_id.code not in medias_obj.dict.keys():
                        return 0
                return rubrica.specific_quantity * \
                    rubrica.specific_percentual / 100 * \
                    rubrica.specific_amount

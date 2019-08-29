# -*- coding: utf-8 -*-
# Copyright 2019 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from __future__ import (absolute_import, division,
                        print_function, unicode_literals)

from openerp import api, fields, models, _
from openerp.exceptions import Warning, ValidationError


class HrContractBenefit(models.Model):
    _name = b'hr.contract.benefit'
    _description = 'Benefícios'
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    def _get_default_contract(self):
        if self.env.user.has_group('base.group_hr_user'):
            return False
        return self.env.user.employee_ids[0].contract_id

    state = fields.Selection(
        selection=[
            ('draft', 'Rascunho'),
            ('waiting', 'Aguardando aprovação'),
            ('validated', 'Aprovado'),
            ('exception', 'Negado'),
            ('cancel', 'Cancelado'),
        ],
        string='Situação',
        default='draft',
        track_visibility='onchange',
        readonly=True,
    )
    name = fields.Char(
        compute='_compute_benefit_name'
    )
    benefit_type_id = fields.Many2one(
        comodel_name='hr.benefit.type',
        string='Tipo Benefício',
        index=True,
        required=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
        track_visibility='onchange'
    )
    date_start = fields.Date(
        string='Início de vigência',
        index=True,
        track_visibility='onchange',
        states={'draft': [('readonly', False)]},
        readonly=True,
        default=fields.Date.context_today,
    )
    date_stop = fields.Date(
        string='Fim de vigência',
        index=True,
        track_visibility='onchange'
    )
    contract_id = fields.Many2one(
        comodel_name='hr.contract',
        required=True,
        index=True,
        string='Contrato',
        track_visibility='onchange',
        states={'draft': [('readonly', False)]},
        readonly=True,
        default=_get_default_contract,
    )
    employee_id = fields.Many2one(
        comodel_name='hr.employee',
        related='contract_id.employee_id',
        readonly=True,
        index=True,
        store=True,
        string='Colaborador',
    )
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        index=True,
        required=True,
        string='Beneficiário',
        track_visibility='onchange',
        states={'draft': [('readonly', False)]},
        readonly=True,
        oldname='beneficiary_id',
    )
    active = fields.Boolean(
        string='Ativo',
        default=True,
        readonly=True,
        track_visibility='onchange'
    )
    attachment_ids = fields.Many2many(
        comodel_name='ir.attachment',
        relation='hr_contract_benefit_att_rel',
        column1='benefit_id',
        column2='attachment_id',
        string='Anexos',
        track_visibility='onchange',
        states={'draft': [('readonly', False)]},
        readonly=True,
    )
    exception_message = fields.Text(
        string='Motivo da exceção na apuração',
        readonly=True,
        track_visibility='onchange'
    )
    line_ids = fields.Many2many(
        comodel_name='hr.contract.benefit.line',
        column1='hr_contract_benefit_id',
        column2='hr_contract_benefit_line_id',
        relation='contract_benefitiary_rel',
        string='Apurações',
        readonly=True,
    )
    line_count = fields.Integer(
        "# Apurações", compute='_compute_line_count',
        readonly=True,
    )

    @api.one
    @api.constrains('employee_id', 'benefit_type_id', 'partner_id')
    def valida_funcionario(self):
        self.ensure_one()
        if self.employee_id and self.benefit_type_id and self.partner_id:

            benefit_ids = self.search([
                ('benefit_type_id.deduction_rule_id', '=',
                 self.benefit_type_id.deduction_rule_id.id),
                ('benefit_type_id.income_rule_id', '=',
                 self.benefit_type_id.income_rule_id.id),
                ('partner_id', '=', self.partner_id.id),
            ]) - self

            if benefit_ids:
                raise ValidationError(
                    _('Este beneficiário já possui um benefício '
                      'ativo para a rúbrica %s' % self.benefit_type_id.name)
                )

            if (self.employee_id.tipo == 'funcionario' and not
                    self.benefit_type_id.beneficiario_funcionario):
                raise ValidationError(
                    _('Funcionários não são permitidos para este benefício')
                )

            if (self.employee_id.tipo == 'autonomo' and not
                    self.benefit_type_id.beneficiario_autonomo):
                raise ValidationError(
                    _('Autônomo não são permitido para este benefício')
                )

            if (self.employee_id.tipo == 'terceirizado' and not
                    self.benefit_type_id.beneficiario_terceiro):
                raise ValidationError(
                    _('Terceirizados não são permitido para este benefício')
                )

            if (self.employee_id.tipo == 'cedido' and not
                    self.benefit_type_id.beneficiario_cedido):
                raise ValidationError(
                    _('Cedidos não são permitido para este benefício')
                )

            if self.partner_id.is_employee_dependent:
                raise ValidationError(
                    _('Dependentes não são permitidos para este benefício')
                )

    @api.onchange('employee_id')
    def onchange_employee_id(self):
        if self.employee_id:
            allowed_partner_ids = self.env['res.partner']
            allowed_partner_ids |= self.employee_id.address_home_id
            allowed_partner_ids |= \
                self.employee_id.dependent_ids.mapped('partner_id')
            return {
                'domain': {
                    'partner_id': [('id', '=', allowed_partner_ids.ids)]},
            }

    @api.multi
    def _compute_line_count(self):
        for record in self:
            record.line_count = len(record.line_ids)

    @api.one
    @api.constrains('date_start', 'date_stop')
    def _check_valid_date_interval(self):
        if self.date_stop and self.date_stop < self.date_start:
            raise Warning(
                _('Data final menor que data inicial'))

    @api.one
    @api.constrains('date_stop')
    def _check_date_stop_active(self):
        today = fields.Date.today()
        if self.date_stop and self.date_stop <= today:
            self.active = False

    @api.one
    @api.constrains("date_start", "date_stop", "benefit_type_id",
                    "partner_id")
    def _check_dates(self):
        domain = [
            ('id', '!=', self.id),
            ('benefit_type_id', '=', self.benefit_type_id.id),
            ('partner_id', '=', self.partner_id.id),
            ('date_start', '<=', self.date_start),
            '|',
            ('date_stop', '=', False),
            ('date_stop', '>=', self.date_start),
        ]
        overlap = self.search(domain)
        if overlap:
            raise Warning(
                _('Já existe um tipo de benefício '
                  'com o mesmo nome e com datas'
                  ' que sobrepõem essa'))

    @api.multi
    @api.depends(
        'benefit_type_id', 'partner_id', 'date_start', 'date_stop')
    def _compute_benefit_name(self):
        for record in self:
            if not record.partner_id or \
                    not record.benefit_type_id:
                record.name = 'Novo'
                continue
            name = '%s - %s' % (
                record.partner_id.name or '',
                record.benefit_type_id.name or '')
            if record.date_start and not record.date_stop:
                name += ' (a partir de %s)' % record.date_start
            elif record.date_start and record.date_stop:
                name += ' (de %s até %s)' % (record.date_start,
                                             record.date_stop)
            record.name = name

    @api.model
    def _agrupar_beneficios(self):

        result = {}

        contract_model = self.env['hr.contract']
        benefit_type_model = self.env['hr.benefit.type']

        sql = """SELECT contract_id, benefit_type_id, array_agg(id)
            FROM hr_contract_benefit
            WHERE active='t' and state='validated'
            GROUP BY contract_id, benefit_type_id"""
        self.env.cr.execute(sql)

        for contract_id, benefit_type_id, \
                benefit_ids in self.env.cr.fetchall():
            contract = contract_model.browse(contract_id)
            benefit_type = benefit_type_model.browse(benefit_type_id)

            benefits = self.search(
                [('id', 'in', benefit_ids)]
            )

            result[(contract, benefit_type)] = benefits

        return result

    @api.multi
    def gerar_prestacao_contas(self, period_id=False):
        if not period_id:
            period_id = self.env['account.period'].find()

        beneficios_agrupados = self._agrupar_beneficios()

        result = self.env['hr.contract.benefit.line']

        for contract_id, benefit_type_id in beneficios_agrupados:

            benefit_line_id = self.env['hr.contract.benefit.line'].create({
                'benefit_type_id': benefit_type_id.id,
                'contract_id': contract_id.id,
                'period_id': period_id.id,
                'beneficiary_ids': [(6, 0,
                                     beneficios_agrupados[
                                         (contract_id, benefit_type_id)
                                     ].ids)],
                # TODO: Talvez transformar em um metodo para valdiar as datas.
                #   Ou tratar no SQL acima
            })

            if not benefit_type_id.line_need_clearance:
                try:
                    benefit_line_id.amount_base = benefit_line_id.amount_benefit
                    benefit_line_id.button_send_receipt()
                except Exception as e:
                    raise ValidationError(_(
                        "Verifique as configurações do benefit.type %s"
                        "\nErro: %s" % (benefit_type_id.name, str(e))
                    ))
            result |= benefit_line_id

        return result

    @api.multi
    def button_send_receipt(self):
        for record in self:
            if (record.benefit_type_id.need_approval_file and
                    not record.attachment_ids):
                raise Warning(_("""\nPara enviar para aprovação é necessário
                 anexar o comprovante"""))

            if not record.benefit_type_id.need_approval:
                record.state = 'validated'
            else:
                record.state = 'waiting'

    @api.multi
    def button_approve_receipt(self):
        for record in self:
            if record.benefit_type_id.need_approval and not \
                    self.env.user.has_group('base.group_hr_user'):
                raise Warning(
                    _("\nFavor solicitar a aprovação de um gerente")
                )
            record.state = 'validated'

    @api.multi
    def button_exception_receipt(self):
        if self.env.user.has_group('base.group_hr_user'):
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'wizard.benefit.exception.cause',
                'view_mode': 'form',
                'view_type': 'form',
                'res_id': False,
                'target': 'new',
            }

    @api.multi
    def button_back_draft(self):
        for record in self:
            if record.state in ['exception', 'cancel']:
                record.state = 'draft'

    @api.multi
    def button_cancel(self):
        for record in self:
            record.state = 'cancel'
            record.date_stop = fields.Date.today()

    @api.multi
    def unlink(self):
        for record in self:
            if record.state not in 'draft':
                raise Warning(
                    _('Você não pode deletar um registro aprovado')
                )
        return super(HrContractBenefit, self).unlink()

    def _validate_benefit(self, vals):

        if self.env.user.has_group('base.group_hr_user') and \
                vals.get('state') == 'waiting':
            vals.update({'state': 'validated'})

    @api.multi
    def write(self, vals):
        self._validate_benefit(vals)
        return super(HrContractBenefit, self).write(vals)

    @api.model
    def create(self, vals):
        self._validate_benefit(vals)
        return super(HrContractBenefit, self).create(vals)

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

    def action_view_benefit_lines(self, cr, uid, ids, context=None):
        benefit = self.pool.get('hr.contract.benefit').browse(cr, uid, ids)
        return {
            'name': _('Prestação de contas'),
            'view_type': 'tree,form',
            'view_mode': 'tree,form',
            'res_model': 'hr.contract.benefit.line',
            'context': context,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', benefit.line_ids.ids)]
        }

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
        ondelete='restrict',
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
        ondelete='restrict',
        index=True,
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
    insurance_beneficiary_ids = fields.One2many(
        comodel_name='benefit.insurance.beneficiary',
        inverse_name='benefit_id',
        string='Beneficiários do Seguro de Vida',
        track_visibility='onchange'
    )
    beneficiary_list = fields.Boolean(
        related='benefit_type_id.beneficiary_list'
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

            if self.contract_id.categoria not in \
                    self.benefit_type_id.contract_category_ids.mapped('name'):
                raise ValidationError(
                    _('Este funcionário não possui uma categoria de '
                      'contrato apta para o tipo de benefício escolhido.')
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

        partner_domain = ('partner_id', '=', self.partner_id.id)
        if not self.partner_id:
            partner_domain = ('contract_id', '=', self.contract_id.id)

        domain = [
            ('id', '!=', self.id),
            ('benefit_type_id', '=', self.benefit_type_id.id),
            partner_domain,
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
            if not record.partner_id:
                if record.beneficiary_list:
                    record.name = '{} - {}'.format(
                        record.employee_id.name or '',
                        record.benefit_type_id.name or ''
                    )
                    continue
                elif not record.benefit_type_id:
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
        benefit_line_model = self.env['hr.contract.benefit.line']

        for contract_id, benefit_type_id in beneficios_agrupados:
            tmp_result = self.env['hr.contract.benefit.line']
            vals = {
                'benefit_type_id': benefit_type_id.id,
                'contract_id': contract_id.id,
                'period_id': period_id.id,
                # TODO: Talvez transformar em um metodo para valdiar as datas.
                #   Ou tratar no SQL acima
            }

            grouped_benefit_ids = beneficios_agrupados[
                (contract_id, benefit_type_id)]

            if benefit_type_id.line_group_benefits:

                vals.update({
                    'beneficiary_ids': [(6, 0, grouped_benefit_ids.ids)],
                })
                tmp_result |= benefit_line_model.create(vals)
                result |= tmp_result
            else:
                for beneficio in grouped_benefit_ids:
                    vals.update({
                        'beneficiary_ids': [(6, 0, beneficio.ids)],
                    })
                    tmp_result |= benefit_line_model.create(vals)
                    result |= tmp_result

            if not benefit_type_id.line_need_clearance:
                try:
                    for benefit_line_id in tmp_result:
                        benefit_line_id.amount_base = \
                            benefit_line_id.amount_benefit
                        benefit_line_id.button_send_receipt()
                except Exception as e:
                    raise ValidationError(_(
                        "Verifique as configurações do benefit.type %s"
                        "\nErro: %s" % (benefit_type_id.name, str(e))
                    ))

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

    def _post_beneficiary_message(self, vals):
        msg = ''
        for item in vals:
            line = self.env['benefit.insurance.beneficiary'].browse(item[1])
            if item[0] == 4 and not item[2]:
                continue
            elif item[0] == 2:
                msg += 'Beneficiário {} foi excluído.' \
                       ' <br/><br/>'.format(line.beneficiary_name)
            elif item[0] == 0 and item[2]:
                msg += 'Novo beneficiário: {} ({}%). <br/>' \
                       '<br/>'.format(item[2].get('beneficiary_name'),
                                      item[2].get('benefit_percent'))
            elif item[0] == 1 and item[2]:
                for key, value in item[2].iteritems():
                    if key == 'beneficiary_name':
                        msg += 'Nome de beneficiário atualizado ' \
                               'de %s para %s <br/>' % (
                            line.beneficiary_name, value)
                    elif key == 'benefit_percent':
                        msg += 'Porcentagem do benefício do(a) ' \
                               '{} atualizado para {} % <br/>'.format(
                            line.beneficiary_name, value)
                msg += '<br/>'
        self.message_post(msg)

    @api.multi
    def write(self, vals):
        self._validate_benefit(vals)
        if vals.get('insurance_beneficiary_ids'):
            self._post_beneficiary_message(
                vals.get('insurance_beneficiary_ids'))
        return super(HrContractBenefit, self).write(vals)

    @api.model
    def create(self, vals):
        self._validate_benefit(vals)
        hr_users = self.env.ref('base.group_hr_user').users
        partner_ids = [user.partner_id.id for user in hr_users]
        vals.update({
            'message_follower_ids': partner_ids
        })
        return super(HrContractBenefit, self).create(vals)

    @api.constrains('insurance_beneficiary_ids')
    def _constrains_benefit_percent(self):
        for record in self:
            total_percent = sum([line.benefit_percent for
                                 line in record.insurance_beneficiary_ids])
            if total_percent > 100:
                raise ValidationError(
                    _('A porcentagem total de recebimento dos beneficiários '
                      'do Seguro de Vida é maior que 100%'.format(
                        total_percent))
                )

    @api.onchange('benefit_type_id')
    def _onchange_benefit_type(self):
        for record in self:
            if record.beneficiary_list:
                record.partner_id = False
            elif not record.beneficiary_list:
                record.insurance_beneficiary_ids = False

    @api.model
    def _needaction_domain_get(self):
        res = super(HrContractBenefit, self)._needaction_domain_get()
        return ['|'] + res + [('state', '=', 'waiting')]


class HrContractBenefitInsuranceBeneficiary(models.Model):
    _name = b'benefit.insurance.beneficiary'

    benefit_id = fields.Many2one(
        comodel_name='hr.contract.benefit',
        string='Benefício relacionado'
    )
    beneficiary_name = fields.Char(
        string='Beneficiário do seguro'
    )
    benefit_percent = fields.Integer(
        string='Porcentagem para o beneficiário'
    )

    @api.multi
    def compute_display_name(self):
        for record in self:
            record.display_name = record.beneficiary_name + \
                                  '({}%)'.format(str(record.benefit_percent))

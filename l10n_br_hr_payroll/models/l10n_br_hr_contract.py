# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models, _
from openerp.exceptions import Warning as UserError
from openerp.exceptions import ValidationError
from pybrasil.data import formata_data

STATES = [
    ('draft', 'Rascunho'),
    ('applied', 'Aplicada')
]

CHANGE_TYPE = [
    ('remuneracao', u'Remuneração'),
    ('jornada', u'Jornada'),
    ('cargo-atividade', u'Cargo/Atividade'),
    ('filiacao-sindical', u'Filiação Sindical'),
    ('lotacao-local', u'Lotação/Local de trabalho'),
]


class HrContractChangeReason(models.Model):

    _name = 'l10n_br_hr.contract.change_reason'
    _description = u"Motivo de alteração contratual"

    name = fields.Char(u"Motivo")


class HrContractChange(models.Model):

    _name = 'l10n_br_hr.contract.change'
    _rec_name = 'nome_alteracao'
    _description = u'Alteração contratual'
    _inherit = 'hr.contract'
    _order = 'change_date desc, contract_id'

    nome_alteracao = fields.Char(
        string='Nome de exibição',
    )

    name = fields.Char(
        string='Nome do contrato',
    )

    contract_id = fields.Many2one(
        comodel_name='hr.contract',
        string='Contrato',
        ondelete='cascade',
    )

    change_type = fields.Selection(
        selection=CHANGE_TYPE,
        string=u"Tipo de alteração contratual",
    )

    change_reason_id = fields.Many2one(
        comodel_name='l10n_br_hr.contract.change_reason',
        string=u"Motivo", required=True,
    )

    change_date = fields.Date(
        string=u'Data da alteração',
        required=True,
        help=u'Alteração deverá ser aplicada apartir dessa data',
    )

    change_date_reference = fields.Date(
        string=u'Data de referência',
        required=True,
        help=u'Data que indica inicio da validade da alteração',
        default=fields.Date.today,
    )

    change_history_ids = fields.Many2many(
        comodel_name='l10n_br_hr.contract.change',
        inverse_name='contract_id',
        string=u"Histórico",
        compute='_get_change_history',
    )

    employee_id = fields.Many2one(
        string='Employee',
        comodel_name='hr.employee',
        required=False
    )

    type_id = fields.Many2one(
        string='Contract Type',
        comodel_name='hr.contract.type',
        required=False
    )

    state = fields.Selection(
        string=u'Alteração aplicada',
        selection=STATES,
        default='draft'
    )

    user_id = fields.Many2one(
        comodel_name='res.users',
        string='Alterado por',
        default=lambda self: self.env.user,
    )

    lotacao_id = fields.Many2one(
        comodel_name='res.company',
        string='Lotação',
    )

    @api.depends('contract_id', 'change_history_ids')
    def _get_change_history(self):
        change_type = self.change_type
        full_history = self.search([
            ('contract_id', '=', self.contract_id.id),
            ('change_type', '=', change_type),
            ('state', '=', 'applied')
        ])
        self.change_history_ids = full_history

    @api.onchange('contract_id')
    def _onchange_contract_id(self):
        contract = self.contract_id
        self.name = contract.name
        self.change_date = fields.Date.today()
        self.notes = contract.notes
        if self.change_type == 'remuneracao':
            self.wage = contract.wage
        elif self.change_type == 'jornada':
            self.working_hours = contract.working_hours
            self.schedule_pay = contract.schedule_pay
            self.monthly_hours = contract.monthly_hours
            self.weekly_hours = contract.weekly_hours
        elif self.change_type == 'cargo-atividade':
            self.job_id = contract.job_id
            self.type_id = contract.type_id
        elif self.change_type == 'filiacao-sindical':
            self.union = contract.union
            self.union_cnpj = contract.union_cnpj
            self.union_entity_code = contract.union_entity_code
            self.discount_union_contribution = \
                contract.discount_union_contribution
            self.month_base_date = contract.month_base_date
        elif self.change_type == 'lotacao-local':
            self.lotacao_id = contract.company_id
            # self.lotacao_cliente_fornecedor = contract.lotacao_cliente_fornecedor
            # self.month_base_data = contract.month_base_data

    def _gerar_dicionario_dados(self, change):
        contract = change.contract_id
        reason = \
            self.env.ref('l10n_br_hr_payroll.'
                         'l10n_br_hr_contract_change_valores_iniciais')
        vals = {
            'contract_id': contract.id,
            'change_date': contract.date_start,
            'change_reason_id': reason.id,
            'wage': contract.wage,
            'struct_id': change.struct_id.id,
            'state': 'applied',
            'name': change.nome_alteracao,
        }

        if change.change_type == 'jornada':
            vals.update(working_hours=contract.working_hours.id)
        elif change.change_type == 'cargo-atividade':
            vals.update(
                job_id=contract.job_id.id,
                type_id=contract.type_id.id,
            )
        elif change.change_type == 'filiacao-sindical':
            vals.update(
                union=contract.union,
                union_cnpj=contract.union_cnpj,
                union_entity_code=contract.union_entity_code,
                discount_union_contribution=
                contract.discount_union_contribution,
                month_base_date=contract.month_base_date
            )
        elif change.change_type == 'lotacao-local':
            vals.update(
                lotacao_id=contract.company_id.id,
                # payment_mode_id=contract.payment_mode_id.id,
            )

        return vals

    @api.multi
    def verificar_primeira_alteracao(self):
        """
        Se for primeira alteração do contrato criar uma alteração para 
        registrar dados iniciais do contrato
        :return: 
        """
        for change in self:

            contract = change.contract_id
            # Buscar se existe alterações anteriores
            domain = [
                ('id', '!=', change.id),
                ('change_type', '=', change.change_type),
                ('contract_id', '=', contract.id),
                ('state', '=', 'applied'),
            ]
            alteracoes_anteriores = self.search_count(domain)

            # se nao existir alterações anteriores, criar a primeira alteração
            # com registro dos dados iniciais do contrato.
            if not alteracoes_anteriores:
                vals = self._gerar_dicionario_dados(change)

                # Criar o registro inicial
                self.create(vals)

    @api.multi
    def apply_contract_changes(self):
        """
        Aplica a alteração no contrato, e se for a primeira alteração daquele 
        tipo cria um registro de alteração inicial.  
        :return: 
        """
        for alteracao in self:
            # Verificar se ja existe alguma alteracao do mesmo tipo
            alteracao.verificar_primeira_alteracao()
            # alias para o contrato corrente
            contract = alteracao.contract_id
            if alteracao.change_type == 'remuneracao':
                contract.wage = alteracao.wage
            elif alteracao.change_type == 'jornada':
                contract.working_hours = alteracao.working_hours
                contract.schedule_pay = alteracao.schedule_pay
                contract.monthly_hours = alteracao.monthly_hours
                contract.weekly_hours = alteracao.weekly_hours
            elif alteracao.change_type == 'cargo-atividade':
                contract.job_id = alteracao.job_id
                contract.with_context(alteracaocontratual=True).employee_id.job_id = \
                    alteracao.job_id
                contract.type_id = alteracao.type_id
            elif self.change_type == 'filiacao-sindical':
                contract.union = alteracao.union
                contract.union_cnpj = alteracao.union_cnpj
                contract.union_entity_code = alteracao.union_entity_code
                contract.discount_union_contribution = \
                    alteracao.discount_union_contribution
                contract.month_base_date = alteracao.month_base_date
            elif self.change_type == 'lotacao-local':
                # Setar variavel de contexto para indicar que a alteração
                # partiu do menu de alterações contratuais.
                contract.with_context(
                    alteracaocontratual=True).company_id = \
                    alteracao.lotacao_id
                # contract.lotacao_cliente_fornecedor = \
                #     alteracao.lotacao_cliente_fornecedor
                # contract.month_base_data = alteracao.month_base_data
            self.state = 'applied'

    @api.multi
    def action_back_to_draft(self):
        """
        Permitir Suporte Voltar alterações para Rascunho, 
        desfazendo a alteração no contrato
        :return: 
        """
        for alteracao in self:
            # verificar se selecionou a ultima alteracao, pois nao sera
            # possível desfazer alterações que nao forem a ultima
            ultima_alteracao = self.search([
                ('change_type', '=', alteracao.change_type),
                ('contract_id', '=', alteracao.contract_id.id),
                ('state', '=', 'applied'),
            ], order='change_date DESC', limit=1)

            if not ultima_alteracao.id == self.id:
                raise UserError(
                    u'Só é possível desfazer a última alteração contratual.'
                    u'\nA última alteração é do dia %s' %
                    formata_data(ultima_alteracao.change_date))

            # Aplicar a penultima alteração contratual
            penultima_alteracao = self.search([
                ('id', '!=', alteracao.id),
                ('change_type', '=', alteracao.change_type),
                ('contract_id', '=', alteracao.contract_id.id),
                ('state', '=', 'applied'),
            ], order='change_date DESC', limit=1)

            # Se nao tiver uma alteração anterior, isso é,
            # se for a primeira alteração contratual não é possível desfazer
            if not penultima_alteracao:
                raise UserError(
                    u'Não é possível desfazer a primeira alteração contratual.'
                    u'\nA primeira alteração contem as informações iniciais '
                    u'do contrato.')

            penultima_alteracao.apply_contract_changes()
            self.state = 'draft'

    @api.model
    def create(self, vals):
        # Criação de um nome para o _rec_name
        # PS.: Nao consegui criar um campo computed. =(
        change_type = vals.get('change_type') or \
                      self.env.context.get('default_change_type')
        if change_type and vals.get('contract_id') and \
                vals.get('change_date'):
            contrato_id = \
                self.env['hr.contract'].browse(vals.get('contract_id'))
            nome_contrato = \
                'Contrato ' + contrato_id.nome_contrato[:6] + ' ' + \
                contrato_id.employee_id.name
            nome_alteracao = \
                u'Alteração de ' + \
                dict(CHANGE_TYPE).get(change_type) + \
                ' ' +  u'em ' + \
                formata_data(vals.get('change_date')) + ' ' + \
                nome_contrato
            vals.update({
                'nome_alteracao' : nome_alteracao,
                'name': nome_alteracao,
                'change_type': change_type,
            })
        return super(HrContractChange, self).create(vals)

    @api.multi
    def unlink(self):
        for alteracao in self:
            if alteracao.state in ['applied'] and \
                    not self.env.user.has_group('base.group_no_one'):
                raise ValidationError(_('You can\'t delete applied changes!'))
        return super(HrContractChange, self).unlink()

    @api.constrains('change_date')
    def _check_date(self):
        '''
        Não permitir incluir uma alteração de remuneração 
        com data anterior a última
        :return: 
        '''
        ultima_alteracao = self.search([
            ('id', '!=', self.id),
            ('change_type', '=', self.change_type),
            ('contract_id', '=', self.contract_id.id),
            ('state', '=', 'applied'),
        ], order='change_date DESC', limit=1)

        if ultima_alteracao and \
                        self.change_date <= ultima_alteracao.change_date:
            raise UserError(
                u'Não é possível criar uma alteração contratual com '
                u'data inferior à última alteração.'
                u'\n Data da última alteração contratual: %s' %
                formata_data(ultima_alteracao.change_date))

# -*- coding: utf-8 -*-
# Copyright 2018 ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models
from openerp.exceptions import Warning, MissingError

MODELS = [
    ('hr.salary.rule', 'Rúbricas Holerite'),
    ('account.invoice', 'Nota Fiscal'),
]


class AccountEvent(models.Model):
    _name = 'account.event'

    state = fields.Selection(
        string='State',
        selection=[
            ('open', 'Aberto'),
            ('validate', 'Validado'),
            ('generated', 'Lançamentos Gerados'),
            ('done', 'Contabilizado'),
            ('reversed', 'Revertido'),
        ],
        default='open',
    )

    tipo = fields.Selection(
        string='Tipo de Evento',
        selection=[
            ('normal', 'Folha Normal'),
            ('decimo_terceiro', u'13º Salário'),
            ('adiantamento_13', u'Adiantamento 13º Salário'),
            ('provisao_ferias', 'Provisão de Férias'),
            ('provisao_decimo_terceiro', 'Provisão de Décimo Terceiro'),
            ('rescisao', 'Rescisão'),
            ('ferias', 'Férias'),
            ('ressarcimento', 'Ressarcimento'),
            ('nfe', 'Nota Fiscal'),
        ],
        help="Identificar o tipo da origem do Evento.",
    )

    account_event_line_ids = fields.One2many(
        string='Event Lines',
        comodel_name='account.event.line',
        inverse_name='account_event_id',
    )

    data = fields.Date(
        string='Data',
    )

    ref = fields.Char(
        string='Ref'
    )

    name = fields.Char(
        string='Name',
        compute='compute_name',
    )

    origem = fields.Reference(
        string=u'Origem',
        selection=MODELS,
    )

    account_event_reversao_id = fields.Many2one(
        string='Evento de reversão',
        comodel_name='account.event',
    )

    account_event_to_revert_id = fields.Many2one(
        string='Evento Para reversão',
        comodel_name='account.event',
    )

    account_event_revert = fields.Boolean(
        string='Reverter Ultimo Evento?',
    )

    account_event_template_id = fields.Many2one(
        string='Roteiro Contábil',
        comodel_name='account.event.template',
    )

    account_move_ids = fields.One2many(
        string=u'Lançamentos',
        comodel_name='account.move',
        inverse_name='account_event_id',
    )

    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Empresa'
    )

    @api.multi
    def compute_name(self):
        """
        """
        for record in self:
            name = ''

            if record.ref:
                name += record.ref

            try:
                if record.origem and record.origem.name:
                    name += ' - {}'.format(record.origem.name)
            except MissingError:
                name += ' - ORIGEM INVÁLIDO'

            record.name = name

    def gerar_eventos(self, lines):
        """
        [{      # CAMPO CODE E VALOR OBRIGATORIO
            'code': 'LIQUIDO',
            'valor': 123,
                # INCREMENTAR DICIONARIO PARA COMPOR
                # HISTORICO PADRAO
            'name': 'Liquido do Holerite' }
         {      # CAMPO CODE E VALOR OBRIGATORIO
            'code': 'INSS',
            'valor': 621.03
                # INCREMENTAR DICIONARIO PARA COMPOR
                # HISTORICO PADRAO
            'name': 'Desconto de INSS'}
        ],

        :return:
        """

        for line in lines:
            line.update(account_event_id=self.id)
            self.env['account.event.line'].create(line)

    @api.multi
    def button_reverter_lancamentos(self):
        """
        Reverter Lançamentos do Evento Contábil
        """
        for record in self:
            data =  record.env.context.get('data', fields.Date.today())
            account_event_reversao_id = record.copy({
                'data': data,
                'ref': 'Reversão do Evento: {}'.format(record.ref),
                'origem': '{},{}'.format('account.event', record.id),
            })

            record.account_event_reversao_id = account_event_reversao_id

            record.account_move_ids.reverter_lancamento(
                account_event_reversao_id)

            record.state = 'reversed'

    def criar_lancamentos(self, vals):
        """
        :param vals:
        :return:
        """
        account_move_ids = self.env['account.move']
        for lancamento in vals:
            account_move_ids += account_move_ids.create(lancamento)
        return account_move_ids

    def _preparar_dados(self):
        dados = {}

        dados['ref'] = self.ref
        dados['data'] = self.data

        period = self.env['account.period']
        dados['period_id'] = period.find(self.data).id
        dados['lines'] = []

        for line in self.account_event_line_ids:
            vals = {
                'event_line_id': line.id,
                'code': line.code,
                'name': line.name,
                'description': line.description,
                'valor': line.valor,
            }

            # Adicionar a origem do evento no dicionario para
            # compor historico padrao
            vals.update(line.account_event_id.origem.read()[0])

            if line.conta_debito_exclusivo_id:
                vals['conta_debito_exclusivo_id'] = \
                    line.conta_debito_exclusivo_id.id
            if line.conta_credito_exclusivo_id:
                vals['conta_credito_exclusivo_id'] = \
                    line.conta_credito_exclusivo_id.id

            dados['lines'].append(vals)

        return dados

    @api.multi
    def gerar_contabilizacao(self):
        """
        Rotina principal:
        """
        for record in self:
            dados = record._preparar_dados()
            record.account_event_template_id.validar_dados(dados)

            account_move_ids = \
                record.account_event_template_id.preparar_dados_lancamentos(
                    dados)

            account_move_ids = record.criar_lancamentos(account_move_ids)

            record.account_move_ids = account_move_ids

            # reverter evento
            if record.account_event_to_revert_id:
                record.account_event_to_revert_id.with_context(
                    {'data': record.data}).button_reverter_lancamentos()

            record.state = 'generated'

    @api.multi
    def validar_evento(self):
        '''
        Valida se existe roteiro contábil selecionado e se os códigos dos
        eventos a serem lançados estão contidos no roteiro.

        :return:
        '''
        for record in self:
            if not record.account_event_template_id:
                raise Warning(u'Por favor, selecione um Roteiro Contábil.')

            template = record.account_event_template_id
            event_line_ids = record.account_event_line_ids.mapped('code')
            template_event_line_ids = \
                template.account_event_template_line_ids.mapped('codigo')

            mensagem = ''

            # Em casaos de reversão
            if record.account_event_template_id.account_event_revert:
                if not record.account_event_to_revert_id:

                    mensagem += \
                        u'<h3>Roteiro selecionado foi configurado para ' \
                        u'reverter último evento válido. Configure o evento' \
                        u' a ser revertido ou clique em "Continuar" ' \
                        u'para não reverter nenhum evento.</h3>'

            # Verifica se os códigos dos eventos estão contidos no template
            if not set(event_line_ids).issubset(template_event_line_ids):
                # Busca itens faltantes
                falta_list = list(
                    filter(lambda x: x not in template_event_line_ids,
                           event_line_ids))

                mensagem += u'\n\n\n Os códigos abaixo não estão contidos ' \
                            u'no roteiro escolhido. Deseja prosseguir?\n\n'

                # Formata os itens em uma string para serem exibidos
                mensagem += ''.join(
                    '<li>{};</li>\n'.format(cod) if cod != falta_list[-1]
                    else '<li>{}.</li>'.format(cod) for cod in falta_list)

                account_event_wizard_id = self.env['account.event.wizard'].\
                    create({'faltantes': mensagem})

                return {
                    'type': 'ir.actions.act_window',
                    'name': 'Códigos faltando no roteiro',
                    'res_model': 'account.event.wizard',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_id': account_event_wizard_id.id,
                    'target': 'new',
                }

            record.state = 'validate'

    @api.multi
    def unlink(self):
        for record in self:
            record.account_move_ids.unlink()
        return super(AccountEvent, self).unlink()

    @api.multi
    def postar_lancamentos(self):
        for record in self:
            for move in record.account_move_ids:
                move.post()

            if record.account_event_to_revert_id:
                record.account_event_to_revert_id.\
                    account_event_reversao_id.postar_lancamentos()

            record.state = 'done'

    @api.multi
    def retornar_aberto(self):
        for record in self:
            for move in record.account_move_ids:
                move.button_return()

            record.account_move_ids.unlink()

            record.state = 'open'

    @api.onchange('account_event_template_id', 'data')
    def onchange_account_event_template_id(self):
        for record in self:

            # Definir se o evento reverterá outro
            if record.account_event_template_id:
                record.account_event_revert = \
                    record.account_event_template_id.account_event_revert

            if record.account_event_revert and record.data:

                evento_para_to_revert = self.search([
                    ('account_event_template_id', '=', record.account_event_template_id.id),
                    ('company_id','=', record.company_id.id),
                    ('data','<', record.data),
                ], order='data DESC', limit=1)

                if evento_para_to_revert:
                    record.account_event_to_revert_id = evento_para_to_revert


class AccountEventWizard(models.TransientModel):
    _name = 'account.event.wizard'

    faltantes = fields.Html(
        string='Códigos que não constam no roteiro',
        readonly=True
    )

    @api.multi
    def validar_codigos_roteiro(self):
        '''

        Continua para alteração do status.
        :return:
        '''
        active_ids = self._context.get('active_ids', [])

        self.env['account.event'].browse(active_ids).state = 'validate'

# Copyright (C) 2012-Today - KMEE (<http://kmee.com.br>).
#  @author Luis Felipe Miléo - mileo@kmee.com.br
#  @author Renato Lima - renato.lima@akretion.com.br
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.addons import decimal_precision as dp
from odoo.exceptions import ValidationError, UserError

from ..constants import (
    AVISO_FAVORECIDO,
    CODIGO_FINALIDADE_TED,
    COMPLEMENTO_TIPO_SERVICO,
    FORMA_LANCAMENTO,
    TIPO_SERVICO,
    BOLETO_ESPECIE,
)


class AccountPaymentMode(models.Model):
    _name = 'account.payment.mode'
    _inherit = ['account.payment.mode', 'mail.thread']

    instructions = fields.Text(
        string='Instruções de cobrança',
    )

    invoice_print = fields.Boolean(
        string='Gerar relatorio na conclusão da fatura?'
    )

    condition_issuing_paper = fields.Selection(
        selection=[
            ('1', 'Banco emite e Processa'),
            ('2', 'Cliente emite e banco processa')],
        string='Condição Emissão de Papeleta',
        default='1',
    )

    communication_2 = fields.Char(
        string='Comunicação para o sacador avalista',
    )

    service_type = fields.Selection(
        selection=TIPO_SERVICO,
        string='Tipo de Serviço',
        help='Campo G025 do CNAB',
    )

    release_form = fields.Selection(
        selection=FORMA_LANCAMENTO,
        string='Forma Lançamento',
        help='Campo G029 do CNAB',
    )

    code_convetion = fields.Char(
        string='Código do Convênio no Banco',
        size=20,
        help='Campo G007 do CNAB',
        track_visibility='always',
    )

    doc_finality_code = fields.Selection(
        selection=COMPLEMENTO_TIPO_SERVICO,
        string='Complemento do Tipo de Serviço',
        help='Campo P005 do CNAB',
    )

    ted_finality_code = fields.Selection(
        selection=CODIGO_FINALIDADE_TED,
        string='Código Finalidade da TED',
        help='Campo P011 do CNAB',
    )

    complementary_finality_code = fields.Char(
        string='Código de finalidade complementar',
        size=2,
        help='Campo P013 do CNAB',
    )

    favored_warning = fields.Selection(
        selection=AVISO_FAVORECIDO,
        string='Aviso ao Favorecido',
        help='Campo P006 do CNAB',
        default=0,
    )

    # A exportação CNAB não se encaixa somente nos parâmetros de
    # débito e crédito.
    boleto_wallet = fields.Char(
        string='Carteira',
        size=3,
        track_visibility='always',
    )

    boleto_modality = fields.Char(
        string='Modalidade',
        size=2,
        track_visibility='always',
    )

    boleto_variation = fields.Char(
        string='Variação',
        size=2,
        track_visibility='always',
    )

    boleto_accept = fields.Selection(
        selection=[
            ('S', 'Sim'),
            ('N', 'Não')],
        string='Aceite',
        default='N',
        track_visibility='always',
    )

    boleto_species = fields.Selection(
        selection=BOLETO_ESPECIE,
        string='Espécie do Título',
        default='01',
        track_visibility='always',
    )

    # Na configuração ou implementação de outros campos é
    # melhor seguir a idéia abaixo pois os campos não são usados com
    # frequencia e incluir um campo do tipo Char permitindo que seja
    # informado o valor de acordo com a configuração do Boleto ao
    # invês de diversos campos do Tipo Select para cada Banco parece
    # ser melhor.
    # [ Deixado manualmente, pois cada banco parece ter sua tabela.
    # ('0', u'Sem instrução'),
    # ('1', u'Protestar (Dias Corridos)'),
    # ('2', u'Protestar (Dias Úteis)'),
    # ('3', u'Não protestar'),
    # ('7', u'Negativar (Dias Corridos)'),
    # ('8', u'Não Negativar')
    # ]
    boleto_protest_code = fields.Char(
        string='Código de Protesto',
        default='0',
        help='Código adotado pela FEBRABAN para identificar o tipo '
             'de prazo a ser considerado para o protesto.',
        track_visibility='always',
    )

    boleto_days_protest = fields.Char(
        string='Número de Dias para Protesto',
        size=2,
        help='Número de dias decorrentes após a data de vencimento '
             'para inicialização do processo de cobrança via protesto.',
        track_visibility='always',
    )

    generate_own_number = fields.Boolean(
        string='Gerar nosso número?',
        default=True,
        help='Dependendo da carteira, banco, etc. '
             'O nosso número pode ser gerado pelo banco.',
    )

    product_tax_id = fields.Many2one(
        comodel_name='product.product',
        string='Taxa Adicional',
        track_visibility='always',
    )

    product_tax_account_id = fields.Many2one(
        comodel_name='account.account',
        string='Conta de Taxa do Produto',
        help='Conta padrão para a Taxa do Produto',
        track_visibility='always',
    )

    cnab_sequence_id = fields.Many2one(
        comodel_name='ir.sequence',
        string='Sequencia do Arquivo CNAB',
        track_visibility='always',
    )

    boleto_byte_idt = fields.Char(
        string='Byte IDT',
        size=1,
        help='Byte de identificação do cedente do bloqueto '
             'utilizado para compor o nosso número, '
             'usado pelos bancos Sicred/Unicred e Sicoob.',
        track_visibility='always',
    )

    boleto_post = fields.Char(
        string='Posto da Cooperativa de Crédito',
        size=2,
        help='Código do Posto da Cooperativa de Crédito,'
             ' usado pelos bancos Sicred/Unicred e Sicoob.',
        track_visibility='always',
    )

    # Field used to make invisible banks specifics fields
    bank_code_bc = fields.Char(
        related='fixed_journal_id.bank_id.code_bc',
    )

    own_number_sequence_id = fields.Many2one(
        comodel_name='ir.sequence',
        string='Sequência do Nosso Número',
        help='Para usar essa Sequencia é preciso definir o campo Tipo do '
             'Nosso Número como Sequencial Único por Carteira no cadastro da '
             'empresa',
        track_visibility='always',
    )

    # Field used to make invisible own_number_sequence_id
    own_number_type = fields.Selection(
        related='fixed_journal_id.company_id.own_number_type',
    )

    boleto_interest_code = fields.Char(
        string='Código da Mora',
        size=1,
        help='Código adotado pela FEBRABAN para identificação '
             'do tipo de pagamento de mora de juros.',
        track_visibility='always',
    )

    boleto_interest_perc = fields.Float(
        string='Percentual de Juros de Mora',
        digits=dp.get_precision('Account'),
        track_visibility='always',
    )

    # TODO - criar outro campo para separar a Conta Contabil de Multa ?
    #  o valor vem somado ao Juros Mora no retorno do cnab 400 unicred,
    #  isso seria o padrão dos outros bancos ?
    interest_fee_account_id = fields.Many2one(
        comodel_name='account.account',
        string='Conta Contabil de Juros Mora e Multa',
        help='Conta padrão para Juros Mora',
        track_visibility='always',
    )

    boleto_fee_code = fields.Char(
        string='Código da Multa',
        size=1,
        help='Código adotado pela FEBRABAN para identificação '
             'do tipo de pagamento de multa.',
        track_visibility='always',
    )

    boleto_fee_perc = fields.Float(
        string='Percentual de Multa',
        digits=dp.get_precision('Account'),
        track_visibility='always',
    )

    boleto_discount_perc = fields.Float(
        string=u"Percentual de Desconto até a Data de Vencimento",
        digits=dp.get_precision('Account'),
        track_visibility='always',
    )

    discount_account_id = fields.Many2one(
        comodel_name='account.account',
        string='Conta Contabil de Desconto',
        help='Conta padrão para Desconto',
        track_visibility='always',
    )

    rebate_account_id = fields.Many2one(
        comodel_name='account.account',
        string='Conta Contabil de Abatimanto',
        help='Conta padrão para Abatimento',
        track_visibility='always',
    )

    tariff_charge_account_id = fields.Many2one(
        comodel_name='account.account',
        string='Conta Contabil Tarifa Bancaria',
        help='Conta padrão para a Tarifa Bancaria',
        track_visibility='always',
    )

    # TODO: Campos many2many não estão sendo registrados pelo track_visibility.
    #  Debate no Odoo https://github.com/odoo/odoo/issues/10149
    #  Modulo na OCA v10 que faria isso
    #  https://github.com/OCA/social/tree/10.0/mail_improved_tracking_value
    #  Migração do Modulo ainda para a v11
    #  https://github.com/OCA/social/pull/254
    #  Devemos incluir esse modulo nas Dependencias OCA do repo e se necessário
    #  fazer essa migração da 12 para poder usa-lo aqui.
    # Podem existir diferentes codigos, mesmo no 240
    cnab_liq_return_move_code_ids = fields.Many2many(
        comodel_name='l10n_br_cnab.return.move.code',
        relation='l10n_br_cnab_return_liquidity_move_code_rel',
        column1='cnab_liq_return_move_code_id',
        column2='payment_mode_id',
        string='CNAB Liquidity Return Move Code',
        track_visibility='always',
    )

    # Codigo de Remessa/Inclusão de Registro Detalhe Liberado
    cnab_sending_code_id = fields.Many2one(
        comodel_name='l10n_br_cnab.mov.instruction.code',
        string='Sending Movement Instruction Code',
        help='Sending Movement Instruction Code',
        track_visibility='always',
    )

    # Codigo para Título/Pagamento Direto ao Fornecedor -Baixar
    cnab_write_off_code_id = fields.Many2one(
        comodel_name='l10n_br_cnab.mov.instruction.code',
        string='Write Off Movement Instruction Code',
        help='Write Off Movement Instruction Code',
        track_visibility='always',
    )

    # Codigo para Alteração do Valor do Titulo
    cnab_code_change_title_value_id = fields.Many2one(
        comodel_name='l10n_br_cnab.mov.instruction.code',
        string='Change Title Value Movement Instruction Code',
        help='CNAB Movement Instruction Code for Change Title Value.',
        track_visibility='always',
    )

    # Codigo para Alteração da Data de Vencimento
    cnab_code_change_maturity_date_id = fields.Many2one(
        comodel_name='l10n_br_cnab.mov.instruction.code',
        string='Change Maturity Date Movement Instruction Code',
        help='CNAB Movement Instruction Code for Change Maturity Date.',
        track_visibility='always',
    )

    # Field used to make invisible banks specifics fields
    bank_id = fields.Many2one(
        related='fixed_journal_id.bank_id',
    )

    @api.constrains(
        'code_convetion',
        'cnab_sequence_id',
        'fixed_journal_id',
        'boleto_wallet',
        'group_lines',
        'generate_move',
        'post_move',
    )
    def _check_cnab_restriction(self):
        for record in self:
            if record.payment_method_code not in ('240', '400', '500'):
                return False
            fields_forbidden_cnab = []
            if record.group_lines:
                fields_forbidden_cnab.append('Group Lines')
            if record.generate_move:
                fields_forbidden_cnab.append('Generated Moves')
            if record.post_move:
                fields_forbidden_cnab.append('Post Moves')

            for field in fields_forbidden_cnab:
                raise ValidationError(
                    _('The Payment Mode can not be used for CNAB with the field'
                      ' %s active. \n Please uncheck it to continue.') % field
                )

            if self.bank_code_bc == '341' and not self.boleto_wallet:
                raise ValidationError('Carteira no banco Itaú é obrigatória')

    @api.onchange('product_tax_id')
    def _onchange_product_tax_id(self):
        if not self.product_tax_id:
            self.tax_account_id = False

    @api.multi
    def get_own_number_sequence(self, inv, numero_documento):
        if inv.company_id.own_number_type == '0':
            # SEQUENCIAL_EMPRESA
            sequence = inv.company_id.own_number_sequence_id.next_by_id()
        elif inv.company_id.own_number_type == '1':
            # SEQUENCIAL_FATURA
            sequence = numero_documento.replace('/', '')
        elif inv.company_id.own_number_type == '2':
            # SEQUENCIAL_CARTEIRA
            sequence = inv.payment_mode_id.own_number_sequence_id.next_by_id()
        else:
            raise UserError(_(
                'Favor acessar aba Cobrança da configuração da'
                ' sua empresa para determinar o tipo de '
                'sequencia utilizada nas cobrancas'
            ))

        return sequence

    @api.constrains('boleto_discount_perc')
    def _check_discount_perc(self):
        for record in self:
            if record.boleto_discount_perc > 100 or\
               record.boleto_discount_perc < 0:
                raise ValidationError(
                    _('O percentual deve ser um valor entre 0 a 100.'))

    @api.onchange('payment_method_id')
    def _onchange_payment_method_id(self):
        for record in self:
            if record.payment_method_code in ('400', '240', '500'):
                # Campos Default que não devem estar marcados no caso CNAB
                record.group_lines = False
                record.generate_move = False
                record.post_move = False
                # Selecionavel na Ordem de Pagamento
                record.payment_order_ok = True

    @api.constrains('own_number_sequence_id')
    def _check_own_number_sequence_id(self):
        for record in self:
            already_in_use = record.search([
                ('id', '!=', record.id),
                ('own_number_sequence_id', '=',
                 record.own_number_sequence_id.id),
            ], limit=1)
            if already_in_use:
                raise ValidationError(
                    _('Sequence Own Number already in use by %s.')
                    % already_in_use.name)

    @api.constrains('cnab_sequence_id')
    def _check_cnab_sequence_id(self):
        for record in self:
            already_in_use = record.search([
                ('id', '!=', record.id),
                ('cnab_sequence_id', '=',
                 record.cnab_sequence_id.id),
            ])

            if already_in_use:
                raise ValidationError(
                    _('Sequence CNAB Sequence already in use by %s.')
                    % already_in_use.name)

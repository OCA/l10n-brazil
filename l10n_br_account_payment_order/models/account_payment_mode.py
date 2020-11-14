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
    _inherit = 'account.payment.mode'

    internal_sequence_id = fields.Many2one(
        comodel_name='ir.sequence',
        string='Sequência',
    )

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

    cnab_percent_interest = fields.Float(
        string='Percentual de Juros',
        digits=dp.get_precision('Account'),
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
    )

    boleto_modality = fields.Char(
        string='Modalidade',
        size=2,
    )

    boleto_convetion = fields.Char(
        string='Codigo convênio',
        size=10,
    )

    boleto_variation = fields.Char(
        string='Variação',
        size=2,
    )

    boleto_cnab_code = fields.Char(
        string='Código Cnab',
        size=20,
    )

    boleto_accept = fields.Selection(
        selection=[
            ('S', 'Sim'),
            ('N', 'Não')],
        string='Aceite',
        default='N',
    )

    boleto_type = fields.Selection(
        selection=[],
        string='Boleto',
    )

    boleto_species = fields.Selection(
        selection=BOLETO_ESPECIE,
        string='Espécie do Título',
        default='01',
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
    )

    boleto_days_protest = fields.Char(
        string='Número de Dias para Protesto',
        size=2,
        help='Número de dias decorrentes após a data de vencimento '
             'para inicialização do processo de cobrança via protesto.'
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
    )

    product_tax_account_id = fields.Many2one(
        comodel_name='account.account',
        string='Conta de Taxa do Produto',
        help='Conta padrão para a Taxa do Produto',
    )

    cnab_sequence_id = fields.Many2one(
        comodel_name='ir.sequence',
        string='Sequencia do CNAB',
    )

    boleto_byte_idt = fields.Char(
        string='Byte IDT',
        size=1,
        help='Byte de identificação do cedente do bloqueto '
             'utilizado para compor o nosso número, '
             'usado pelos bancos Sicred/Unicred e Sicoob.',
    )

    boleto_post = fields.Char(
        string='Posto da Cooperativa de Crédito',
        size=2,
        help='Código do Posto da Cooperativa de Crédito,'
             ' usado pelos bancos Sicred/Unicred e Sicoob.',
    )

    # Field used to make invisible banks specifics fields
    bank_code_bc = fields.Char(
        related='fixed_journal_id.bank_id.code_bc',
    )

    own_number_sequence = fields.Many2one(
        comodel_name='ir.sequence',
        string='Sequência do Nosso Número',
        help='Para usar essa Sequencia é preciso definir o campo Tipo do '
             'Nosso Número como Sequencial Único por Carteira no cadastro da '
             'empresa',
    )

    # Field used to make invisible own_number_sequence
    own_number_type = fields.Selection(
        related='fixed_journal_id.company_id.own_number_type',
    )

    boleto_interest_code = fields.Char(
        string='Código da Mora',
        size=1,
        help='Código adotado pela FEBRABAN para identificação '
             'do tipo de pagamento de mora de juros.',
    )

    boleto_interest_perc = fields.Float(
        string='Percentual de Juros de Mora',
        digits=dp.get_precision('Account'),
    )

    # TODO - criar outro campo para separar a Conta Contabil de Multa ?
    #  o valor vem somado ao Juros Mora no retorno do cnab 400 unicred,
    #  isso seria o padrão dos outros bancos ?
    interest_fee_account_id = fields.Many2one(
        comodel_name='account.account',
        string='Conta Contabil de Juros Mora e Multa',
        help='Conta padrão para Juros Mora',
    )

    boleto_fee_code = fields.Char(
        string='Código da Multa',
        size=1,
        help='Código adotado pela FEBRABAN para identificação '
             'do tipo de pagamento de multa.',
    )

    boleto_fee_perc = fields.Float(
        string='Percentual de Multa',
        digits=dp.get_precision('Account'),
    )

    boleto_discount_perc = fields.Float(
        string=u"Percentual de Desconto até a Data de Vencimento",
        digits=dp.get_precision('Account')
    )

    discount_account_id = fields.Many2one(
        comodel_name='account.account',
        string='Conta Contabil de Desconto',
        help='Conta padrão para Desconto',
    )

    rebate_account_id = fields.Many2one(
        comodel_name='account.account',
        string='Conta Contabil de Abatimanto',
        help='Conta padrão para Abatimento',
    )

    tariff_charge_account_id = fields.Many2one(
        comodel_name='account.account',
        string='Conta Contabil Tarifa Bancaria',
        help='Conta padrão para a Tarifa Bancaria',
    )

    # Foi preciso criar esse campo pois o CNAB 400 não
    # parece padronizado (olhar dados na pasta Data),
    # dessa forma novas implementações
    # do 400 podem ser feitas atraves de cadastro,
    # o CNAB 240 parece ser mais padronizado.
    cnab_liq_return_move_code_ids = fields.Many2many(
        comodel_name='l10n_br_cnab.return.move.code',
        relation='l10n_br_cnab_return_liquidity_move_code_rel',
        column1='cnab_liq_return_move_code_id',
        column2='payment_mode_id',
        string='CNAB Liquidity Return Move Code'
    )
    # TODO - pode ser melhorado ?
    # Só foi possível ter um Domain de forma dinamica,
    #  devido a diferença no caso do 240
    domain_cnab_liq_return_move_code_ids = fields.Many2many(
        comodel_name='l10n_br_cnab.return.move.code',
        relation='domain_l10n_br_cnab_return_liquidity_move_code_rel',
        column1='domain_cnab_liq_return_move_code_id',
        column2='payment_mode_id',
        compute='_get_domain_cnab_liq_return_move_code',
        store=False,
    )
    # Field used to make invisible Inbound or Outbound specifics fields
    payment_type = fields.Selection(related='payment_method_id.payment_type')

    # Codigos de Instrução do Movimento podem variar, 240 mais padronizado
    # TODO - pode ser melhorado ?
    #  Só foi possível ter um Domain de forma dinamica,
    #  devido a diferença no caso do 240
    domain_cnab_mov_instr_code_ids = fields.Many2many(
        comodel_name='l10n_br_cnab.mov.instruction.code',
        relation='domain_l10n_br_cnab_instruction_code_rel',
        column1='domain_cnab_mov_instr_code_id',
        column2='payment_mode_id',
        compute='_get_domain_cnab_mov_instr_code',
        store=False,
    )

    # Codigo de Remessa/Inclusão de Registro Detalhe Liberado
    cnab_sending_code_id = fields.Many2one(
        comodel_name='l10n_br_cnab.mov.instruction.code',
        string='Movement Instruction Sending Code',
        help='Movement Instruction Code for Sending CNAB',
    )

    # Codigo para Título/Pagamento Direto ao Fornecedor -Baixar
    cnab_write_off_code_id = fields.Many2one(
        comodel_name='l10n_br_cnab.mov.instruction.code',
        string='Write Off Movement Instruction Code',
        help='Write Off Movement Instruction Code',
    )

    _sql_constraints = [(
        "internal_sequence_id_unique",
        "unique(internal_sequence_id)",
        _("Sequência já usada! Crie uma sequência unica para cada modo"),
        )
    ]

    @api.constrains(
        'boleto_type',
        'boleto_wallet',
        'boleto_modality',
        'boleto_convetion',
        'boleto_variation',
    )
    def boleto_restriction(self):
        if self.boleto_type == '6' and not self.boleto_wallet:
            raise ValidationError('Carteira no banco Itaú é obrigatória')
        if self.group_lines:
            raise ValidationError(
                _('The Payment mode can not be used for Boleto/CNAB with the group'
                  ' lines active. \n Please uncheck it to continue.')
            )
        if self.generate_move or self.post_move:
            raise ValidationError(
                _('The Payment mode can not be used for Boleto/CNAB with the'
                  ' generated moves or post moves active. \n Please uncheck it'
                  ' to continue.')
            )

    @api.onchange('product_tax_id')
    def _onchange_product_tax_id(self):
        if not self.product_tax_id:
            self.tax_account_id = False

    @api.multi
    def get_own_number_sequence(self, inv, numero_documento):
        if inv.company_id.own_number_type == '0':
            # SEQUENCIAL_EMPRESA
            sequence = inv.company_id.own_number_sequence.next_by_id()
        elif inv.company_id.own_number_type == '1':
            # SEQUENCIAL_FATURA
            sequence = numero_documento.replace('/', '')
        elif inv.company_id.own_number_type == '2':
            # SEQUENCIAL_CARTEIRA
            sequence = inv.payment_mode_id.own_number_sequence.next_by_id()
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
        # CNAB 240, parece ser mais padronizado
        for record in self:
            if record.payment_method_id.code == '240':
                # Valores Padrões de Liquidação/Baixa
                # 06 - Liquidação
                # 09 - Baixa
                # 17 - Liquidação após Baixa ou Liquidação Título não
                # Registrado
                liq_codes = self.env['l10n_br_cnab.return.move.code'].search([
                    ('payment_method_code', '=', '240'),
                    ('code', 'in', ['06', '09', '17'])
                ])
                record.cnab_liq_return_move_code_ids = liq_codes.ids

                # Valor Padrão de Remessa
                # 00 - Inclusão de Registro Detalhe Liberado
                cnab_sending_code = self.env[
                    'l10n_br_cnab.mov.instruction.code'].search([
                        ('payment_method_code', '=', '240'),
                        ('code', '=', '00')])
                record.cnab_sending_code_id = cnab_sending_code.id
                # Valor Padrão de Baixa
                # 23 - Pagamento Direto ao Fornecedor - Baixar
                cnab_write_off_code = self.env[
                    'l10n_br_cnab.mov.instruction.code'].search([
                        ('payment_method_code', '=', '240'),
                        ('code', '=', '23')])
                record.cnab_write_off_code_id = cnab_write_off_code.id

    @api.multi
    @api.depends('payment_method_id', 'bank_code_bc')
    def _get_domain_cnab_liq_return_move_code(self):
        for record in self:
            search_domain = [
                ('payment_method_code', '=', record.payment_method_id.code)]
            if record.payment_method_id.code != '240':
                search_domain.append(
                    ('bank_code_bc', '=', record.bank_code_bc))

            return_codes = self.env[
                'l10n_br_cnab.return.move.code'].search(search_domain)

            record.domain_cnab_liq_return_move_code_ids = return_codes.ids

    @api.multi
    @api.depends('payment_method_id', 'bank_code_bc')
    def _get_domain_cnab_mov_instr_code(self):
        for record in self:
            search_domain = [
                ('payment_method_code', '=', record.payment_method_id.code)]
            if record.payment_method_id.code != '240':
                search_domain.append(
                    ('bank_code_bc', '=', record.bank_code_bc))

            codes = self.env[
                'l10n_br_cnab.mov.instruction.code'].search(search_domain)

            record.domain_cnab_mov_instr_code_ids = codes.ids

# Copyright (C) 2012-Today - KMEE (<http://kmee.com.br>).
#  @author Luis Felipe Miléo - mileo@kmee.com.br
#  @author Renato Lima - renato.lima@akretion.com.br
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.addons import decimal_precision as dp
from odoo.exceptions import ValidationError

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
        default='0001222130126',
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
        'boleto_accept',
    )
    def boleto_restriction(self):
        if self.boleto_type == '6' and not self.boleto_wallet:
            raise ValidationError('Carteira no banco Itaú é obrigatória')

    @api.onchange('product_tax_id')
    def _onchange_product_tax_id(self):
        if not self.product_tax_id:
            self.tax_account_id = False

    @api.multi
    def get_own_number_sequence(self):
        self.ensure_one()
        return self.own_number_sequence.next_by_id()

    @api.constrains('boleto_discount_perc')
    def _check_discount_perc(self):
        for record in self:
            if record.boleto_discount_perc > 100 or\
               record.boleto_discount_perc < 0:
                raise ValidationError(
                    _('O percentual deve ser um valor entre 0 a 100.'))

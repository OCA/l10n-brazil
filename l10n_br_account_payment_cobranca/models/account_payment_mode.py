# © 2012 KMEE INFORMATICA LTDA
#   @author Fernando Marcato <fernando.marcato@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models
from odoo.addons import decimal_precision as dp
from odoo.exceptions import ValidationError

from ..constantes import (AVISO_FAVORECIDO, CODIGO_FINALIDADE_TED,
                          COMPLEMENTO_TIPO_SERVICO, FORMA_LANCAMENTO,
                          TIPO_SERVICO, BOLETO_ESPECIE)


class PaymentMode(models.Model):
    _inherit = "account.payment.mode"

    condicao_emissao_papeleta = fields.Selection(
        [("1", "Banco emite e Processa"), ("2", "Cliente emite e banco processa")],
        "Condição Emissão de Papeleta",
        default="1",
    )
    cnab_percent_interest = fields.Float(
        string="Percentual de Juros", digits=dp.get_precision("Account")
    )
    comunicacao_2 = fields.Char("Comunicação para o sacador avalista")
    tipo_servico = fields.Selection(
        selection=TIPO_SERVICO, string="Tipo de Serviço", help="Campo G025 do CNAB"
    )
    forma_lancamento = fields.Selection(
        selection=FORMA_LANCAMENTO, string="Forma Lançamento", help="Campo G029 do CNAB"
    )
    codigo_convenio = fields.Char(
        size=20,
        string="Código do Convênio no Banco",
        help="Campo G007 do CNAB",
        default="0001222130126",
    )
    codigo_finalidade_doc = fields.Selection(
        selection=COMPLEMENTO_TIPO_SERVICO,
        string="Complemento do Tipo de Serviço",
        help="Campo P005 do CNAB",
    )
    codigo_finalidade_ted = fields.Selection(
        selection=CODIGO_FINALIDADE_TED,
        string="Código Finalidade da TED",
        help="Campo P011 do CNAB",
    )
    codigo_finalidade_complementar = fields.Char(
        size=2, string="Código de finalidade complementar", help="Campo P013 do CNAB"
    )
    aviso_ao_favorecido = fields.Selection(
        selection=AVISO_FAVORECIDO,
        string="Aviso ao Favorecido",
        help="Campo P006 do CNAB",
        default=0,
    )
    # A exportação CNAB não se encaixa somente nos parâmetros de
    # débito e crédito.
    boleto_carteira = fields.Char("Carteira", size=3)
    boleto_modalidade = fields.Char("Modalidade", size=2)
    boleto_convenio = fields.Char("Codigo convênio", size=10)
    boleto_variacao = fields.Char("Variação", size=2)
    boleto_cnab_code = fields.Char("Código Cnab", size=20)
    boleto_aceite = fields.Selection(
        [("S", "Sim"), ("N", "Não")], string="Aceite", default="N"
    )
    boleto_type = fields.Selection(selection=[], string="Boleto")
    boleto_especie = fields.Selection(
        selection=BOLETO_ESPECIE,
        string="Espécie do Título",
        default="01",
    )
    boleto_cod_protesto = fields.Char(
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
        string="Código de Protesto",
        help='Código adotado pela FEBRABAN para identificar o tipo'
             ' de prazo a ser considerado para o protesto.',
        default="0",
    )
    boleto_dias_protesto = fields.Char(
        string="Número de Dias para Protesto", size=2,
        help='Número de dias decorrentes após a data de vencimento'
             ' para inicialização do processo de cobrança via protesto.'
    )
    gera_nosso_numero = fields.Boolean(
        string="Gerar nosso número?",
        help="Dependendo da carteira, banco, etc. "
        "O nosso número pode ser gerado pelo banco.",
        default=True,
    )
    default_account_id = fields.Many2one(
        comodel_name="account.account",
        string="Conta Padrão",
        help="Conta padrão para recebimentos",
    )
    default_tax_account_id = fields.Many2one(
        comodel_name="account.account",
        string="Conta Padrão para Taxas Bancárias",
        help="Conta padrão para recebimentos de Taxas Bancárias",
    )
    product_tax_id = fields.Many2one(
        comodel_name="product.product", string="Taxa Adicional"
    )
    tax_account_id = fields.Many2one(
        comodel_name="account.account",
        string="Conta Padrão",
        help="Conta padrão para Taxa",
    )
    operation_type = fields.Selection(selection_add=[("3", "Cobrança")])
    cnab_sequence_id = fields.Many2one(
        comodel_name='ir.sequence',
        string=u'Sequencia do CNAB')
    boleto_byte_idt = fields.Char(
        string='Byte IDT', size=1,
        help='Byte de identificação do cedente do bloqueto'
             ' utilizado para compor o nosso número,'
             ' usado pelos bancos Sicred/Unicred e Sicoob'
    )
    boleto_posto = fields.Char(
        string='Posto da Cooperativa de Crédito', size=2,
        help='Código do Posto da Cooperativa de Crédito,'
             ' usado pelos bancos Sicred/Unicred e Sicoob.'
    )
    # Field used to make invisible banks specifics fields
    bank_code_bc = fields.Char(related='fixed_journal_id.bank_id.code_bc')
    own_number_sequence = fields.Many2one(
        comodel_name='ir.sequence', string='Sequência do Nosso Número',
        help='Para usar essa Sequencia é preciso definir o campo Tipo do'
             ' Nosso Número como Sequencial Único por Carteira no cadastro da'
             ' empresa ',
    )

    @api.onchange("product_tax_id")
    def _onchange_product_tax_id(self):
        if not self.product_tax_id:
            self.tax_account_id = False

    @api.constrains("product_override")
    def _constrains_product_override(self):
        if self.product_override and self.product_override_value <= 0:
            raise ValidationError("O valor da Taxa deve ser maior que 0 (zero)")

    @api.constrains(
        "boleto_type",
        "boleto_carteira",
        "boleto_modalidade",
        "boleto_convenio",
        "boleto_variacao",
        "boleto_aceite",
    )
    def boleto_restriction(self):
        if self.boleto_type == "6" and not self.boleto_carteira:
            raise ValidationError("Carteira no banco Itaú é obrigatória")

    @api.multi
    def get_own_number_sequence(self):
        self.ensure_one()
        return self.own_number_sequence.next_by_id()

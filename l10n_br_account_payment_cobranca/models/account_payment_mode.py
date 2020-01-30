# © 2012 KMEE INFORMATICA LTDA
#   @author Fernando Marcato <fernando.marcato@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models
from odoo.addons import decimal_precision as dp
from odoo.exceptions import ValidationError

from ..constantes import (AVISO_FAVORECIDO, CODIGO_FINALIDADE_TED,
                          COMPLEMENTO_TIPO_SERVICO, FORMA_LANCAMENTO,
                          TIPO_SERVICO)


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
        selection=FORMA_LANCAMENTO,
        string="Forma Lançamento",
        help="Campo G029 do CNAB",
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
        [
            ("01", "DUPLICATA MERCANTIL"),
            ("02", "NOTA PROMISSÓRIA"),
            ("03", "NOTA DE SEGURO"),
            ("04", "MENSALIDADE ESCOLAR"),
            ("05", "RECIBO"),
            ("06", "CONTRATO"),
            ("07", "COSSEGUROS"),
            ("08", "DUPLICATA DE SERVIÇO"),
            ("09", "LETRA DE CÂMBIO"),
            ("13", "NOTA DE DÉBITOS"),
            ("15", "DOCUMENTO DE DÍVIDA"),
            ("16", "ENCARGOS CONDOMINIAIS"),
            ("17", "CONTA DE PRESTAÇÃO DE SERVIÇOS"),
            ("99", "DIVERSOS"),
        ],
        string="Espécie do Título",
        default="01",
    )
    boleto_protesto = fields.Char(
        # [ Deixado manualmente, pois cada banco parece ter sua tabela.
        # ('0', u'Sem instrução'),
        # ('1', u'Protestar (Dias Corridos)'),
        # ('2', u'Protestar (Dias Úteis)'),
        # ('3', u'Não protestar'),
        # ('7', u'Negativar (Dias Corridos)'),
        # ('8', u'Não Negativar')
        # ]
        string="Códigos de Protesto",
        default="0",
    )
    boleto_protesto_prazo = fields.Char("Prazo protesto", size=2)
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

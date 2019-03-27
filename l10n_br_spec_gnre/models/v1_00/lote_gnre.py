# Copyright 2019 Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).
# Generated Wed Mar 27 01:50:56 2019 by generateDS.py(Akretion's branch).
# Python 3.6.7 (default, Oct 22 2018, 11:32:17)  [GCC 8.2.0]
#
import textwrap
from odoo import fields
from .. import spec_models

# Código do Tipo de Identificação do Destinatário:
TIdentificacao = [
    ("1", "1 - CNPJ"),
    ("2", "2 - CPF"),
]

# Tipo Meses do Ano
TMes_c05_referencia = [
    ("01", "01"),
    ("02", "02"),
    ("03", "03"),
    ("04", "04"),
    ("05", "05"),
    ("06", "06"),
    ("07", "07"),
    ("08", "08"),
    ("09", "09"),
    ("10", "10"),
    ("11", "11"),
    ("12", "12"),
]

# Código do tipo de dados dos Campos Extras:
TTipoCampoExtra_campoExtra = [
    ("T", "T - Texto"),
    ("N", "N - Numérico"),
    ("D", "D - Data"),
]

# Tipo Sigla da UF
TUf = [
    ("AC", "AC"),
    ("AL", "AL"),
    ("AM", "AM"),
    ("AP", "AP"),
    ("BA", "BA"),
    ("CE", "CE"),
    ("DF", "DF"),
    ("ES", "ES"),
    ("GO", "GO"),
    ("MA", "MA"),
    ("MG", "MG"),
    ("MS", "MS"),
    ("MT", "MT"),
    ("PA", "PA"),
    ("PB", "PB"),
    ("PE", "PE"),
    ("PI", "PI"),
    ("PR", "PR"),
    ("RJ", "RJ"),
    ("RN", "RN"),
    ("RO", "RO"),
    ("RR", "RR"),
    ("RS", "RS"),
    ("SC", "SC"),
    ("SE", "SE"),
    ("SP", "SP"),
    ("TO", "TO"),
]

# Indicador do Periodo:
periodo_c05_referencia = [
    ("0", "0 – mensal"),
    ("1", "1 – 1a. quinzena"),
    ("2", "2 – 2a. quinzena"),
    ("3", "3 – 1o. decêndio"),
    ("4", "4 – 2o. decêndio"),
    ("5", "5 – 3o. decêndio"),
]


class TDadosGNRE(spec_models.AbstractSpecMixin):
    _description = 'tdadosgnre'
    _name = 'gnre.10.tdadosgnre'
    _generateds_type = 'TDadosGNREType'
    _concrete_rec_name = 'gnre_c01_UfFavorecida'

    gnre10_TDadosGNRE_guias_id = fields.Many2one(
        "gnre.10.guias")
    gnre10_c01_UfFavorecida = fields.Selection(
        TUf,
        string="Código da UF Favorecida",
        xsd_required=True,
        help="Código da UF Favorecida. (Utilizar a Tabela do IBGE)")
    gnre10_c02_receita = fields.Char(
        string="Código da Receita.")
    gnre10_c25_detalhamentoReceita = fields.Char(
        string="Código do Detalhamento da Receita.")
    gnre10_c26_produto = fields.Char(
        string="Código do Produto.")
    gnre10_c27_tipoIdentificacaoEmitente = fields.Selection(
        TIdentificacao,
        string="Código do Tipo de Identificação do Emitente",
        help="Código do Tipo de Identificação do Emitente:")
    gnre10_c03_idContribuinteEmitente = fields.Many2one(
        "gnre.10.c03_idcontribuinteemitente",
        string="c03_idContribuinteEmitente",
        help="Número do Documento de Identificação do Contribuinte"
        "\nEmitente.")
    gnre10_c28_tipoDocOrigem = fields.Char(
        string="Código do Tipo de Documento de Origem")
    gnre10_c04_docOrigem = fields.Char(
        string="Número do Documento de Origem.")
    gnre10_c06_valorPrincipal = fields.Monetary(
        digits=2, string="Valor Original da Guia.")
    gnre10_c10_valorTotal = fields.Monetary(
        digits=2, string="Valor total da guia",
        help="Valor total da guia (valor original + encargos).")
    gnre10_c14_dataVencimento = fields.Date(
        string="Data de vencimento da guia.")
    gnre10_c15_convenio = fields.Char(
        string="Número do convênio.")
    gnre10_c16_razaoSocialEmitente = fields.Char(
        string="Nome da firma ou a Razão Social do Contribuinte")
    gnre10_c17_inscricaoEstadualEmitente = fields.Char(
        string="Inscrição Estadual do Contribuinte na UF favorecida")
    gnre10_c18_enderecoEmitente = fields.Char(
        string="Endereço do Contribuinte.")
    gnre10_c19_municipioEmitente = fields.Char(
        string="Código do Município de localização do Contribuinte",
        help="Código do Município de localização do Contribuinte.(Utilizar"
        "\na tabela do IBGE)")
    gnre10_c20_ufEnderecoEmitente = fields.Selection(
        TUf,
        string="Código da UF do Contribuinte.")
    gnre10_c21_cepEmitente = fields.Char(
        string="CEP do Contribuinte.")
    gnre10_c22_telefoneEmitente = fields.Char(
        string="Telefone do contribuinte.")
    gnre10_c34_tipoIdentificacaoDestinatario = fields.Selection(
        TIdentificacao,
        string="Tipo de Identificação do Destinatário")
    gnre10_c35_idContribuinteDestinatario = fields.Many2one(
        "gnre.10.c35_idcontribuintedestinatario",
        string="c35_idContribuinteDestinatario",
        help="Número do Documento de Identificação do Contribuinte"
        "\nDestinatário.")
    gnre10_c36_inscricaoEstadualDestinatario = fields.Char(
        string="Inscrição Estadual do Contribuinte na UF favorecida")
    gnre10_c37_razaoSocialDestinatario = fields.Char(
        string="Nome da firma ou a Razão Social do Contribuinte")
    gnre10_c38_municipioDestinatario = fields.Char(
        string="Código do Município de Destino",
        help="Código do Município de Destino.(Utilizar a tabela do IBGE)")
    gnre10_c33_dataPagamento = fields.Date(
        string="Data prevista de pagamento informada pelo contribuinte")
    gnre10_c05_referencia = fields.Many2one(
        "gnre.10.c05_referencia",
        string="c05_referencia")
    gnre10_c39_camposExtras = fields.Many2one(
        "gnre.10.c39_camposextras",
        string="c39_camposExtras")


class TLote_GNRE(spec_models.AbstractSpecMixin):
    _description = 'tlote_gnre'
    _name = 'gnre.10.tlote_gnre'
    _generateds_type = 'TLote_GNRE'
    _concrete_rec_name = 'gnre_guias'

    gnre10_guias = fields.Many2one(
        "gnre.10.guias",
        string="guias", xsd_required=True)


class C03_idContribuinteEmitente(spec_models.AbstractSpecMixin):
    "Número do Documento de Identificação do Contribuinte Emitente."
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'gnre.10.c03_idcontribuinteemitente'
    _generateds_type = 'c03_idContribuinteEmitenteType'
    _concrete_rec_name = 'gnre_CNPJ'

    gnre10_choice1 = fields.Selection([
        ('gnre10_CNPJ', 'CNPJ'),
        ('gnre10_CPF', 'CPF')],
        "CNPJ/CPF",
        default="gnre10_CNPJ")
    gnre10_CNPJ = fields.Char(
        choice='1',
        string="Número do CNPJ do Contribuinte",
        xsd_required=True)
    gnre10_CPF = fields.Char(
        choice='1',
        string="Número do CPF do Contribuinte",
        xsd_required=True)


class C05_referencia(spec_models.AbstractSpecMixin):
    "Informações de período de apuração"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'gnre.10.c05_referencia'
    _generateds_type = 'c05_referenciaType'
    _concrete_rec_name = 'gnre_periodo'

    gnre10_periodo = fields.Selection(
        periodo_c05_referencia,
        string="Indicador do Periodo",
        help="Indicador do Periodo:"
        "\n0 – mensal;"
        "\n1 – 1a. quinzena;"
        "\n2 – 2a. quinzena;"
        "\n3 – 1o. decêndio;"
        "\n4 – 2o. decêndio;"
        "\n5 – 3o. decêndio;")
    gnre10_mes = fields.Selection(
        TMes_c05_referencia,
        string="Mês de referência da Apuração")
    gnre10_ano = fields.Char(
        string="Ano de referência da Apuração")
    gnre10_parcela = fields.Char(
        string="Parcela de referência da Apuração")


class C35_idContribuinteDestinatario(spec_models.AbstractSpecMixin):
    "Número do Documento de Identificação do Contribuinte Destinatário."
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'gnre.10.c35_idcontribuintedestinatario'
    _generateds_type = 'c35_idContribuinteDestinatarioType'
    _concrete_rec_name = 'gnre_CNPJ'

    gnre10_choice2 = fields.Selection([
        ('gnre10_CNPJ', 'CNPJ'),
        ('gnre10_CPF', 'CPF')],
        "CNPJ/CPF",
        default="gnre10_CNPJ")
    gnre10_CNPJ = fields.Char(
        choice='2',
        string="Número do CNPJ do Contribuinte Destinatário",
        xsd_required=True)
    gnre10_CPF = fields.Char(
        choice='2',
        string="Número do CPF do Contribuinte Destinatário",
        xsd_required=True)


class C39_camposExtras(spec_models.AbstractSpecMixin):
    _description = 'c39_camposextras'
    _name = 'gnre.10.c39_camposextras'
    _generateds_type = 'c39_camposExtrasType'
    _concrete_rec_name = 'gnre_campoExtra'

    gnre10_campoExtra = fields.One2many(
        "gnre.10.campoextra",
        "gnre10_campoExtra_c39_camposExtras_id",
        string="campoExtra", xsd_required=True
    )


class CampoExtra(spec_models.AbstractSpecMixin):
    _description = 'campoextra'
    _name = 'gnre.10.campoextra'
    _generateds_type = 'campoExtraType'
    _concrete_rec_name = 'gnre_codigo'

    gnre10_campoExtra_c39_camposExtras_id = fields.Many2one(
        "gnre.10.c39_camposextras")
    gnre10_codigo = fields.Integer(
        string="codigo", xsd_required=True)
    gnre10_tipo = fields.Selection(
        TTipoCampoExtra_campoExtra,
        string="tipo", xsd_required=True)
    gnre10_valor = fields.Char(
        string="valor", xsd_required=True)


class Guias(spec_models.AbstractSpecMixin):
    _description = 'guias'
    _name = 'gnre.10.guias'
    _generateds_type = 'guiasType'
    _concrete_rec_name = 'gnre_TDadosGNRE'

    gnre10_TDadosGNRE = fields.One2many(
        "gnre.10.tdadosgnre",
        "gnre10_TDadosGNRE_guias_id",
        string="TDadosGNRE", xsd_required=True
    )

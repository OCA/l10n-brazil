# Copyright 2019 Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).
# Generated Tue Sep 24 17:57:37 2019 by generateDS.py(Akretion's branch).
# Python 3.6.7 (default, Oct 22 2018, 11:32:17)  [GCC 8.2.0]
#
import textwrap
from odoo import fields, models

# Tipo Ambiente
TAMB = [
    ("1", "1"),
    ("2", "2"),
]

# Tipo Código da UF da tabela do IBGE
TCODUFIBGE = [
    ("11", "11"),
    ("12", "12"),
    ("13", "13"),
    ("14", "14"),
    ("15", "15"),
    ("16", "16"),
    ("17", "17"),
    ("21", "21"),
    ("22", "22"),
    ("23", "23"),
    ("24", "24"),
    ("25", "25"),
    ("26", "26"),
    ("27", "27"),
    ("28", "28"),
    ("29", "29"),
    ("31", "31"),
    ("32", "32"),
    ("33", "33"),
    ("35", "35"),
    ("41", "41"),
    ("42", "42"),
    ("43", "43"),
    ("50", "50"),
    ("51", "51"),
    ("52", "52"),
    ("53", "53"),
]

# Tipo Modelo Documento Fiscal
TMOD = [
    ("55", "55"),
    ("65", "65"),
]

# Serviço Solicitado
XSERV_INFINUT = [
    ("INUTILIZAR", "INUTILIZAR"),
]


class TInutNFe(models.AbstractModel):
    "Tipo Pedido de Inutilização de Numeração da Nota Fiscal Eletrônica"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'nfe.40.tinutnfe'
    _inherit = 'spec.mixin.nfe'
    _generateds_type = 'TInutNFe'
    _concrete_rec_name = 'nfe40_versao'

    nfe40_versao = fields.Char(
        string="versao", xsd_required=True)
    nfe40_infInut = fields.Many2one(
        "nfe.40.infinut",
        string="infInut", xsd_required=True,
        help="Dados do Pedido de Inutilização de Numeração da Nota Fiscal"
        "\nEletrônica")


class TProcInutNFe(models.AbstractModel):
    "Tipo Pedido de inutilzação de númeração de NF-e processado"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'nfe.40.tprocinutnfe'
    _inherit = 'spec.mixin.nfe'
    _generateds_type = 'TProcInutNFe'
    _concrete_rec_name = 'nfe40_versao'

    nfe40_versao = fields.Char(
        string="versao", xsd_required=True)
    nfe40_inutNFe = fields.Many2one(
        "nfe.40.tinutnfe",
        string="inutNFe", xsd_required=True)
    nfe40_retInutNFe = fields.Many2one(
        "nfe.40.tretinutnfe",
        string="retInutNFe", xsd_required=True)


class TRetInutNFe(models.AbstractModel):
    """Tipo retorno do Pedido de Inutilização de Numeração da Nota Fiscal
    Eletrônica"""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'nfe.40.tretinutnfe'
    _inherit = 'spec.mixin.nfe'
    _generateds_type = 'TRetInutNFe'
    _concrete_rec_name = 'nfe40_versao'

    nfe40_versao = fields.Char(
        string="versao", xsd_required=True)
    nfe40_infInut = fields.Many2one(
        "nfe.40.infinut1",
        string="infInut", xsd_required=True,
        help="Dados do Retorno do Pedido de Inutilização de Numeração da"
        "\nNota Fiscal Eletrônica")


class InfInut(models.AbstractModel):
    """Dados do Pedido de Inutilização de Numeração da Nota Fiscal
    Eletrônica"""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'nfe.40.infinut'
    _inherit = 'spec.mixin.nfe'
    _generateds_type = 'infInutType'
    _concrete_rec_name = 'nfe40_Id'

    nfe40_Id = fields.Char(
        string="Id", xsd_required=True)
    nfe40_tpAmb = fields.Selection(
        TAMB,
        string="Identificação do Ambiente",
        xsd_required=True,
        help="Identificação do Ambiente:"
        "\n1 - Produção"
        "\n2 - Homologação")
    nfe40_xServ = fields.Selection(
        XSERV_INFINUT,
        string="Serviço Solicitado", xsd_required=True)
    nfe40_cUF = fields.Selection(
        TCODUFIBGE,
        string="Código da UF do emitente",
        xsd_required=True)
    nfe40_ano = fields.Char(
        string="Ano de inutilização da numeração",
        xsd_required=True)
    nfe40_CNPJ = fields.Char(
        string="CNPJ do emitente", xsd_required=True)
    nfe40_mod = fields.Selection(
        TMOD,
        string="Modelo da NF-e (55, 65 etc.)",
        xsd_required=True)
    nfe40_serie = fields.Char(
        string="Série da NF-e", xsd_required=True)
    nfe40_nNFIni = fields.Char(
        string="Número da NF-e inicial",
        xsd_required=True)
    nfe40_nNFFin = fields.Char(
        string="Número da NF-e final",
        xsd_required=True)
    nfe40_xJust = fields.Char(
        string="Justificativa do pedido de inutilização",
        xsd_required=True)


class InfInut1(models.AbstractModel):
    """Dados do Retorno do Pedido de Inutilização de Numeração da Nota Fiscal
    Eletrônica"""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'nfe.40.infinut1'
    _inherit = 'spec.mixin.nfe'
    _generateds_type = 'infInutType1'
    _concrete_rec_name = 'nfe40_Id'

    nfe40_Id = fields.Char(
        string="Id")
    nfe40_tpAmb = fields.Selection(
        TAMB,
        string="Identificação do Ambiente",
        xsd_required=True,
        help="Identificação do Ambiente:"
        "\n1 - Produção"
        "\n2 - Homologação")
    nfe40_verAplic = fields.Char(
        string="Versão do Aplicativo que processou a NF",
        xsd_required=True,
        help="Versão do Aplicativo que processou a NF-e")
    nfe40_cStat = fields.Char(
        string="Código do status da mensagem enviada",
        xsd_required=True)
    nfe40_xMotivo = fields.Char(
        string="Descrição literal do status do serviço solicitado",
        xsd_required=True)
    nfe40_cUF = fields.Selection(
        TCODUFIBGE,
        string="Código da UF que atendeu a solicitação",
        xsd_required=True)
    nfe40_ano = fields.Char(
        string="Ano de inutilização da numeração")
    nfe40_CNPJ = fields.Char(
        string="CNPJ do emitente")
    nfe40_mod = fields.Selection(
        TMOD,
        string="Modelo da NF-e (55, etc.)")
    nfe40_serie = fields.Char(
        string="Série da NF-e")
    nfe40_nNFIni = fields.Char(
        string="Número da NF-e inicial")
    nfe40_nNFFin = fields.Char(
        string="Número da NF-e final")
    nfe40_dhRecbto = fields.Datetime(
        string="Data e hora de recebimento",
        xsd_required=True,
        help="Data e hora de recebimento, no formato AAAA-MM-DDTHH:MM:SS."
        "\nDeve ser preenchida com data e hora da gravação no"
        "\nBanco em caso de Confirmação. Em caso de Rejeição,"
        "\ncom data e hora do recebimento do Pedido de"
        "\nInutilização.")
    nfe40_nProt = fields.Char(
        string="Número do Protocolo de Status da NF",
        help="Número do Protocolo de Status da NF-e. 1 posição (1 –"
        "\nSecretaria de Fazenda Estadual 2 – Receita Federal);"
        "\n2 - código da UF - 2 posições ano; 10 seqüencial no"
        "\nano.")

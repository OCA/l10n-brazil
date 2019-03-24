# Copyright 2019 Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).
# Generated Sat Mar 23 23:12:16 2019 by generateDS.py(Akretion's branch).
# Python 3.6.7 (default, Oct 22 2018, 11:32:17)  [GCC 8.2.0]
#
import textwrap
from odoo import fields
from .. import spec_models

# Tipo Ambiente
TAmb = [
    ("1", "1"),
    ("2", "2"),
]

# Tipo Código de orgão (UF da tabela do IBGE + 90 RFB)
TCOrgaoIBGE = [
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
    ("90", "90"),
]

# Tipo Código da UF da tabela do IBGE
# Tipo Modelo Documento Fiscal
# Tipo Sigla da UF
# Tipo Sigla da UF de emissor // acrescentado em 24/10/08
# Tipo Código do Pais
# // PL_005d - 11/08/09
# eliminado
# 4235-LEBUAN, ILHAS -
# acrescentado
# Descrição do Evento - “Carta de Correção”
descEvento_detEvento = [
    ("Carta de Correção", "Carta de Correção"),
    ("Carta de Correcao", "Carta de Correcao"),
]

# Tipo do Evento
tpEvento_infEvento = [
    ("110110", "110110"),
]

# Versão do Tipo do Evento
verEvento_infEvento = [
    ("1.00", "1.00"),
]

# Texto Fixo com as condições de uso da Carta de Correção
xCondUso_detEvento = [
    ("A Carta de Correção é disciplina", "A Carta de Correção é disciplinada "
     "pelo § 1º-A do art. 7º do "
     "Convênio S/N, de 15 de "
     "dezembro de 1970 e pode ser "
     "utilizada para regularização "
     "de erro ocorrido na emissão "
     "de documento fiscal, desde "
     "que o erro não esteja "
     "relacionado com: I - as "
     "variáveis que determinam o "
     "valor do imposto tais como: "
     "base de cálculo, alíquota, "
     "diferença de preço, "
     "quantidade, valor da operação "
     "ou da prestação; II - a "
     "correção de dados cadastrais "
     "que implique mudança do "
     "remetente ou do destinatário; "
     "III - a data de emissão ou de "
     "saída."),
    ("A Carta de Correcao e disciplina", "A Carta de Correcao e disciplinada "
     "pelo paragrafo 1o-A do art. "
     "7o do Convenio S/N, de 15 de "
     "dezembro de 1970 e pode ser "
     "utilizada para regularizacao "
     "de erro ocorrido na emissao "
     "de documento fiscal, desde "
     "que o erro nao esteja "
     "relacionado com: I - as "
     "variaveis que determinam o "
     "valor do imposto tais como: "
     "base de calculo, aliquota, "
     "diferenca de preco, "
     "quantidade, valor da operacao "
     "ou da prestacao; II - a "
     "correcao de dados cadastrais "
     "que implique mudanca do "
     "remetente ou do destinatario; "
     "III - a data de emissao ou de "
     "saida."),
]


class TEnvEvento(spec_models.AbstractSpecMixin):
    "Tipo Lote de Envio"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'cce.10.tenvevento'
    _generateds_type = 'TEnvEvento'
    _concrete_rec_name = 'cce_versao'

    cce10_versao = fields.Char(
        string="versao", xsd_required=True)
    cce10_idLote = fields.Char(
        string="idLote", xsd_required=True)
    cce10_evento = fields.One2many(
        "cce.10.tevento",
        "cce10_evento_TEnvEvento_id",
        string="evento", xsd_required=True
    )


class TEvento(spec_models.AbstractSpecMixin):
    "Tipo Evento"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'cce.10.tevento'
    _generateds_type = 'TEvento'
    _concrete_rec_name = 'cce_versao'

    cce10_evento_TEnvEvento_id = fields.Many2one(
        "cce.10.tenvevento")
    cce10_versao = fields.Char(
        string="versao", xsd_required=True)
    cce10_infEvento = fields.Many2one(
        "cce.10.infevento",
        string="infEvento", xsd_required=True)


class TProcEvento(spec_models.AbstractSpecMixin):
    "Tipo procEvento"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'cce.10.tprocevento'
    _generateds_type = 'TProcEvento'
    _concrete_rec_name = 'cce_versao'

    cce10_versao = fields.Char(
        string="versao", xsd_required=True)
    cce10_evento = fields.Many2one(
        "cce.10.tevento",
        string="evento", xsd_required=True)
    cce10_retEvento = fields.Many2one(
        "cce.10.tretevento",
        string="retEvento", xsd_required=True)


class TRetEnvEvento(spec_models.AbstractSpecMixin):
    "Tipo Retorno de Lote de Envio"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'cce.10.tretenvevento'
    _generateds_type = 'TRetEnvEvento'
    _concrete_rec_name = 'cce_versao'

    cce10_versao = fields.Char(
        string="versao", xsd_required=True)
    cce10_idLote = fields.Char(
        string="idLote", xsd_required=True)
    cce10_tpAmb = fields.Selection(
        TAmb,
        string="Identificação do Ambiente",
        xsd_required=True,
        help="Identificação do Ambiente:"
        "\n1 - Produção"
        "\n2 - Homologação")
    cce10_verAplic = fields.Char(
        string="Versão do Aplicativo que recebeu o Evento",
        xsd_required=True)
    cce10_cOrgao = fields.Selection(
        TCOrgaoIBGE,
        string="Código do òrgao que registrou o Evento",
        xsd_required=True,
        help="Tipo Código de orgão (UF da tabela do IBGE + 90 RFB)")
    cce10_cStat = fields.Char(
        string="Código do status da registro do Evento",
        xsd_required=True)
    cce10_xMotivo = fields.Char(
        string="Descrição literal do status do registro do Evento",
        xsd_required=True)
    cce10_retEvento = fields.One2many(
        "cce.10.tretevento",
        "cce10_retEvento_TRetEnvEvento_id",
        string="retEvento"
    )


class TretEvento(spec_models.AbstractSpecMixin):
    "Tipo retorno do Evento"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'cce.10.tretevento'
    _generateds_type = 'TretEvento'
    _concrete_rec_name = 'cce_versao'

    cce10_retEvento_TRetEnvEvento_id = fields.Many2one(
        "cce.10.tretenvevento")
    cce10_versao = fields.Char(
        string="versao", xsd_required=True)
    cce10_infEvento = fields.Many2one(
        "cce.10.infevento1",
        string="infEvento", xsd_required=True)


class DetEvento(spec_models.AbstractSpecMixin):
    "Evento do carta de correção e1101110"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'cce.10.detevento'
    _generateds_type = 'detEventoType'
    _concrete_rec_name = 'cce_versao'

    cce10_versao = fields.Char(
        string="versao", xsd_required=True)
    cce10_descEvento = fields.Selection(
        descEvento_detEvento,
        string="Descrição do Evento",
        xsd_required=True,
        help="Descrição do Evento - “Carta de Correção”")
    cce10_xCorrecao = fields.Char(
        string="Correção a ser considerada",
        xsd_required=True)
    cce10_xCondUso = fields.Selection(
        xCondUso_detEvento,
        string="Texto Fixo com as condições de uso da Carta de Correção",
        xsd_required=True)


class InfEvento(spec_models.AbstractSpecMixin):
    """Identificação do autor do eventoIdentificador da TAG a ser assinada, a
    regra de formação do Id é:
    “ID” + tpEvento + chave da NF-e + nSeqEvento"""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'cce.10.infevento'
    _generateds_type = 'infEventoType'
    _concrete_rec_name = 'cce_Id'

    cce10_choice1 = fields.Selection([
        ('cce10_CNPJ', 'CNPJ'),
        ('cce10_CPF', 'CPF')],
        "CNPJ/CPF",
        default="cce10_CNPJ")
    cce10_Id = fields.Char(
        string="Id", xsd_required=True)
    cce10_cOrgao = fields.Selection(
        TCOrgaoIBGE,
        string="Código do órgão de recepção do Evento",
        xsd_required=True,
        help="Tipo Código de orgão (UF da tabela do IBGE + 90 RFB)")
    cce10_tpAmb = fields.Selection(
        TAmb,
        string="Identificação do Ambiente",
        xsd_required=True,
        help="Identificação do Ambiente:"
        "\n1 - Produção"
        "\n2 - Homologação")
    cce10_CNPJ = fields.Char(
        choice='1',
        string="CNPJ", xsd_required=True)
    cce10_CPF = fields.Char(
        choice='1',
        string="CPF", xsd_required=True)
    cce10_chNFe = fields.Char(
        string="Chave de Acesso da NF",
        xsd_required=True,
        help="Chave de Acesso da NF-e vinculada ao evento")
    cce10_dhEvento = fields.Datetime(
        string="Data de emissão no formato UTC",
        xsd_required=True,
        help="Data de emissão no formato UTC. AAAA-MM-DDThh:mm:ssTZD")
    cce10_tpEvento = fields.Selection(
        tpEvento_infEvento,
        string="Tipo do Evento", xsd_required=True)
    cce10_nSeqEvento = fields.Char(
        string="Seqüencial do evento para o mesmo tipo de evento",
        xsd_required=True,
        help="Seqüencial do evento para o mesmo tipo de evento. Para"
        "\nmaioria dos eventos será 1, nos casos em que possa"
        "\nexistir mais de um evento, como é o caso da carta de"
        "\ncorreção, o autor do evento deve numerar de forma"
        "\nseqüencial.")
    cce10_verEvento = fields.Selection(
        verEvento_infEvento,
        string="Versão do Tipo do Evento",
        xsd_required=True)
    cce10_detEvento = fields.Many2one(
        "cce.10.detevento",
        string="Evento do carta de correção e1101110",
        xsd_required=True)


class InfEvento1(spec_models.AbstractSpecMixin):
    "Identificação do destinatário da NF-e"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'cce.10.infevento1'
    _generateds_type = 'infEventoType1'
    _concrete_rec_name = 'cce_Id'

    cce10_choice2 = fields.Selection([
        ('cce10_CNPJDest', 'CNPJDest'),
        ('cce10_CPFDest', 'CPFDest')],
        "CNPJDest/CPFDest",
        default="cce10_CNPJDest")
    cce10_Id = fields.Char(
        string="Id")
    cce10_tpAmb = fields.Selection(
        TAmb,
        string="Identificação do Ambiente",
        xsd_required=True,
        help="Identificação do Ambiente:"
        "\n1 - Produção"
        "\n2 - Homologação")
    cce10_verAplic = fields.Char(
        string="Versão do Aplicativo que recebeu o Evento",
        xsd_required=True)
    cce10_cOrgao = fields.Selection(
        TCOrgaoIBGE,
        string="Código do órgão de recepção do Evento",
        xsd_required=True,
        help="Tipo Código de orgão (UF da tabela do IBGE + 90 RFB)")
    cce10_cStat = fields.Char(
        string="Código do status da registro do Evento",
        xsd_required=True)
    cce10_xMotivo = fields.Char(
        string="Descrição literal do status do registro do Evento",
        xsd_required=True)
    cce10_chNFe = fields.Char(
        string="Chave de Acesso NF-e vinculada")
    cce10_tpEvento = fields.Char(
        string="Tipo do Evento vinculado")
    cce10_xEvento = fields.Char(
        string="Descrição do Evento")
    cce10_nSeqEvento = fields.Char(
        string="Seqüencial do evento")
    cce10_CNPJDest = fields.Char(
        choice='2',
        string="CNPJ Destinatário")
    cce10_CPFDest = fields.Char(
        choice='2',
        string="CPF Destiantário")
    cce10_emailDest = fields.Char(
        string="email do destinatário")
    cce10_dhRegEvento = fields.Char(
        string="dhRegEvento", xsd_required=True,
        help="Data e Hora de do recebimento do evento ou do registro do"
        "\nevento formato UTC AAAA-MM-DDThh:mm:ssTZD.")
    cce10_nProt = fields.Char(
        string="Número do protocolo de registro do evento")

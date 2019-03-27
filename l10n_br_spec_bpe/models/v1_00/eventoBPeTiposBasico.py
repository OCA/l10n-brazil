# Copyright 2019 Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).
# Generated Wed Mar 27 02:20:54 2019 by generateDS.py(Akretion's branch).
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

# Tipo Código de orgão (UF da tabela do IBGE + 90 SUFRAMA + 91 RFB + 92
# BRId)
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
    ("91", "91"),
    ("92", "92"),
    ("93", "93"),
]


class TEvento(spec_models.AbstractSpecMixin):
    "Tipo Evento"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'bpe.10.tevento'
    _generateds_type = 'TEvento'
    _concrete_rec_name = 'bpe_versao'

    bpe10_versao = fields.Char(
        string="versao", xsd_required=True)
    bpe10_infEvento = fields.Many2one(
        "bpe.10.infevento",
        string="infEvento", xsd_required=True)


class TProcEvento(spec_models.AbstractSpecMixin):
    "Tipo procEvento"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'bpe.10.tprocevento'
    _generateds_type = 'TProcEvento'
    _concrete_rec_name = 'bpe_versao'

    bpe10_versao = fields.Char(
        string="versao", xsd_required=True)
    bpe10_ipTransmissor = fields.Char(
        string="ipTransmissor")
    bpe10_eventoBPe = fields.Many2one(
        "bpe.10.tevento",
        string="eventoBPe", xsd_required=True)
    bpe10_retEventoBPe = fields.Many2one(
        "bpe.10.tretevento",
        string="retEventoBPe", xsd_required=True)


class TRetEvento(spec_models.AbstractSpecMixin):
    "Tipo retorno do Evento"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'bpe.10.tretevento'
    _generateds_type = 'TRetEvento'
    _concrete_rec_name = 'bpe_versao'

    bpe10_versao = fields.Char(
        string="versao", xsd_required=True)
    bpe10_infEvento = fields.Many2one(
        "bpe.10.infevento1",
        string="infEvento", xsd_required=True)


class DetEvento(spec_models.AbstractSpecMixin):
    "Detalhamento do evento específico"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'bpe.10.detevento'
    _generateds_type = 'detEventoType'
    _concrete_rec_name = 'bpe_versaoEvento'

    bpe10_versaoEvento = fields.Char(
        string="versaoEvento", xsd_required=True)
    bpe10___ANY__ = fields.Char(
        string="__ANY__", xsd_required=True)


class InfEvento(spec_models.AbstractSpecMixin):
    """Identificador da TAG a ser assinada, a regra de formação do Id é:
    “ID” + tpEvento + chave do CT-e + nSeqEvento"""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'bpe.10.infevento'
    _generateds_type = 'infEventoType'
    _concrete_rec_name = 'bpe_Id'

    bpe10_Id = fields.Char(
        string="Id", xsd_required=True)
    bpe10_cOrgao = fields.Selection(
        TCOrgaoIBGE,
        string="Código do órgão de recepção do Evento",
        xsd_required=True,
        help="Tipo Código de orgão (UF da tabela do IBGE + 90 SUFRAMA + 91"
        "\nRFB + 92 BRId)")
    bpe10_tpAmb = fields.Selection(
        TAmb,
        string="Identificação do Ambiente",
        xsd_required=True,
        help="Identificação do Ambiente:"
        "\n1 - Produção"
        "\n2 - Homologação")
    bpe10_CNPJ = fields.Char(
        string="CNPJ do emissor do evento",
        xsd_required=True)
    bpe10_chBPe = fields.Char(
        string="Chave de Acesso do BP",
        xsd_required=True,
        help="Chave de Acesso do BP-e vinculado ao evento")
    bpe10_dhEvento = fields.Datetime(
        string="Data e Hora do Evento",
        xsd_required=True,
        help="Data e Hora do Evento, formato UTC (AAAA-MM-DDThh:mm:ssTZD)")
    bpe10_tpEvento = fields.Char(
        string="Tipo do Evento", xsd_required=True)
    bpe10_nSeqEvento = fields.Char(
        string="Seqüencial do evento para o mesmo tipo de evento",
        xsd_required=True,
        help="Seqüencial do evento para o mesmo tipo de evento. Para"
        "\nmaioria dos eventos será 1, nos casos em que possa"
        "\nexistir mais de um evento o autor do evento deve"
        "\nnumerar de forma seqüencial.")
    bpe10_detEvento = fields.Many2one(
        "bpe.10.detevento",
        string="Detalhamento do evento específico",
        xsd_required=True)


class InfEvento1(spec_models.AbstractSpecMixin):
    _description = 'infevento1'
    _name = 'bpe.10.infevento1'
    _generateds_type = 'infEventoType1'
    _concrete_rec_name = 'bpe_Id'

    bpe10_Id = fields.Char(
        string="Id")
    bpe10_tpAmb = fields.Selection(
        TAmb,
        string="Identificação do Ambiente",
        xsd_required=True,
        help="Identificação do Ambiente:"
        "\n1 - Produção"
        "\n2 - Homologação")
    bpe10_verAplic = fields.Char(
        string="Versão do Aplicativo que recebeu o Evento",
        xsd_required=True)
    bpe10_cOrgao = fields.Selection(
        TCOrgaoIBGE,
        string="Código do órgão de recepção do Evento",
        xsd_required=True,
        help="Tipo Código de orgão (UF da tabela do IBGE + 90 SUFRAMA + 91"
        "\nRFB + 92 BRId)")
    bpe10_cStat = fields.Char(
        string="Código do status da registro do Evento",
        xsd_required=True)
    bpe10_xMotivo = fields.Char(
        string="Descrição literal do status do registro do Evento",
        xsd_required=True)
    bpe10_chBPe = fields.Char(
        string="Chave de Acesso BP-e vinculado")
    bpe10_tpEvento = fields.Char(
        string="Tipo do Evento vinculado")
    bpe10_xEvento = fields.Char(
        string="Descrição do Evento")
    bpe10_nSeqEvento = fields.Char(
        string="Seqüencial do evento")
    bpe10_dhRegEvento = fields.Datetime(
        string="dhRegEvento",
        help="Data e Hora de do recebimento do evento ou do registro do"
        "\nevento formato AAAA-MM-DDThh:mm:ssTZD")
    bpe10_nProt = fields.Char(
        string="Número do protocolo de registro do evento")

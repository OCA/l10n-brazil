# Copyright 2019 Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).
# Generated Wed Mar 27 03:42:49 2019 by generateDS.py(Akretion's branch).
# Python 3.6.7 (default, Oct 22 2018, 11:32:17)  [GCC 8.2.0]
#
import textwrap
from odoo import fields
from .. import spec_models


class Reinf(spec_models.AbstractSpecMixin):
    "EFD-Reinf"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'efdreinf.01.reinf'
    _generateds_type = 'Reinf'
    _concrete_rec_name = 'efdreinf_evtCPRB'

    efdreinf01_evtCPRB = fields.Many2one(
        "efdreinf.01.evtcprb",
        string="evtCPRB", xsd_required=True)


class EvtCPRB(spec_models.AbstractSpecMixin):
    """Evento da contribuição previdenciária sobre a receita bruta -
    CPRBIdentificação única do evento"""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'efdreinf.01.evtcprb'
    _generateds_type = 'evtCPRBType'
    _concrete_rec_name = 'efdreinf_id'

    efdreinf01_id = fields.Char(
        string="id", xsd_required=True)
    efdreinf01_ideEvento = fields.Many2one(
        "efdreinf.01.ideevento",
        string="Informações de identificação do evento",
        xsd_required=True)
    efdreinf01_ideContri = fields.Many2one(
        "efdreinf.01.idecontri",
        string="Informações de identificação do contribuinte",
        xsd_required=True)
    efdreinf01_infoCPRB = fields.Many2one(
        "efdreinf.01.infocprb",
        string="infoCPRB", xsd_required=True,
        help="Informação da Contribuição Previdenciária sobre a Receita"
        "\nBruta")


class IdeContri(spec_models.AbstractSpecMixin):
    "Informações de identificação do contribuinte"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'efdreinf.01.idecontri'
    _generateds_type = 'ideContriType'
    _concrete_rec_name = 'efdreinf_tpInsc'

    efdreinf01_nrInsc = fields.Char(
        string="Informar o CNPJ apenas com a Raiz/Base de oito posições",
        xsd_required=True,
        help="Informar o CNPJ apenas com a Raiz/Base de oito posições,"
        "\nexceto se natureza jurídica do declarante for de"
        "\nadministração pública direta federal ([101-5], [104-0], [107-4] e"
        "\n[116-3]), situação em que o campo deve"
        "\nser preenchido com o CNPJ completo com 14 posições.")


class IdeEstab(spec_models.AbstractSpecMixin):
    """Registro que identifica o estabelecimento que auferiu a receita
    bruta."""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'efdreinf.01.ideestab'
    _generateds_type = 'ideEstabType'
    _concrete_rec_name = 'efdreinf_tpInscEstab'

    efdreinf01_tpInscEstab = fields.Integer(
        string="tpInscEstab",
        xsd_required=True,
        help="Preencher com o código correspondente ao tipo de inscrição:"
        "\nDeve ser igual a [1] (CNPJ) ou [4] CNO")
    efdreinf01_nrInscEstab = fields.Char(
        string="nrInscEstab",
        xsd_required=True,
        help="Preencher com o número de inscrição do estabelecimento"
        "\npertencente ao contribuinte declarante, de acordo com"
        "\no tipo de inscrição indicado no campo {tpInscEstab}.")
    efdreinf01_vlrRecBrutaTotal = fields.Char(
        string="vlrRecBrutaTotal",
        xsd_required=True)
    efdreinf01_vlrCPApurTotal = fields.Char(
        string="vlrCPApurTotal",
        xsd_required=True)
    efdreinf01_vlrCPRBSuspTotal = fields.Char(
        string="vlrCPRBSuspTotal")
    efdreinf01_tipoCod = fields.One2many(
        "efdreinf.01.tipocod",
        "efdreinf01_tipoCod_ideEstab_id",
        string="tipoCod", xsd_required=True,
        help="Registro que apresenta o valor total da receita por tipo de"
        "\ncódigo de atividade econômica"
    )


class IdeEvento(spec_models.AbstractSpecMixin):
    "Informações de identificação do evento"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'efdreinf.01.ideevento'
    _generateds_type = 'ideEventoType'
    _concrete_rec_name = 'efdreinf_indRetif'

    efdreinf01_nrRecibo = fields.Char(
        string="nrRecibo")
    efdreinf01_perApur = fields.Date(
        string="Informar o ano/mês",
        xsd_required=True,
        help="Informar o ano/mês (formato AAAA-MM) de referência das"
        "\ninformações")
    efdreinf01_tpAmb = fields.Integer(
        string="tpAmb", xsd_required=True)
    efdreinf01_verProc = fields.Char(
        string="verProc", xsd_required=True)


class InfoCPRB(spec_models.AbstractSpecMixin):
    "Informação da Contribuição Previdenciária sobre a Receita Bruta"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'efdreinf.01.infocprb'
    _generateds_type = 'infoCPRBType'
    _concrete_rec_name = 'efdreinf_ideEstab'

    efdreinf01_ideEstab = fields.Many2one(
        "efdreinf.01.ideestab",
        string="ideEstab", xsd_required=True,
        help="Registro que identifica o estabelecimento que auferiu a"
        "\nreceita bruta.")


class InfoProc(spec_models.AbstractSpecMixin):
    "Informações de processos relacionados a Suspensão da CPRB."
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'efdreinf.01.infoproc'
    _generateds_type = 'infoProcType'
    _concrete_rec_name = 'efdreinf_tpProc'

    efdreinf01_infoProc_tipoCod_id = fields.Many2one(
        "efdreinf.01.tipocod")
    efdreinf01_nrProc = fields.Char(
        string="nrProc", xsd_required=True)
    efdreinf01_codSusp = fields.Char(
        string="codSusp")
    efdreinf01_vlrCPRBSusp = fields.Char(
        string="vlrCPRBSusp",
        xsd_required=True)


class TipoAjuste(spec_models.AbstractSpecMixin):
    """Registro a ser preenchido caso a pessoa jurídica tenha de proceder a
    ajustes da contribuição apurada no período,
    decorrentes da legislação tributária da contribuição, de estorno ou de
    outras situações."""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'efdreinf.01.tipoajuste'
    _generateds_type = 'tipoAjusteType'
    _concrete_rec_name = 'efdreinf_tpAjuste'

    efdreinf01_tipoAjuste_tipoCod_id = fields.Many2one(
        "efdreinf.01.tipocod")
    efdreinf01_codAjuste = fields.Integer(
        string="codAjuste", xsd_required=True)
    efdreinf01_vlrAjuste = fields.Char(
        string="vlrAjuste", xsd_required=True)
    efdreinf01_descAjuste = fields.Char(
        string="descAjuste",
        xsd_required=True)
    efdreinf01_dtAjuste = fields.Date(
        string="dtAjuste", xsd_required=True)


class TipoCod(spec_models.AbstractSpecMixin):
    """Registro que apresenta o valor total da receita por tipo de código de
    atividade econômica"""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'efdreinf.01.tipocod'
    _generateds_type = 'tipoCodType'
    _concrete_rec_name = 'efdreinf_codAtivEcon'

    efdreinf01_tipoCod_ideEstab_id = fields.Many2one(
        "efdreinf.01.ideestab")
    efdreinf01_codAtivEcon = fields.Char(
        string="codAtivEcon",
        xsd_required=True)
    efdreinf01_vlrRecBrutaAtiv = fields.Char(
        string="vlrRecBrutaAtiv",
        xsd_required=True)
    efdreinf01_vlrExcRecBruta = fields.Char(
        string="vlrExcRecBruta",
        xsd_required=True)
    efdreinf01_vlrAdicRecBruta = fields.Char(
        string="vlrAdicRecBruta",
        xsd_required=True)
    efdreinf01_vlrBcCPRB = fields.Char(
        string="vlrBcCPRB", xsd_required=True)
    efdreinf01_vlrCPRBapur = fields.Char(
        string="vlrCPRBapur")
    efdreinf01_tipoAjuste = fields.One2many(
        "efdreinf.01.tipoajuste",
        "efdreinf01_tipoAjuste_tipoCod_id",
        string="tipoAjuste",
        help="Registro a ser preenchido caso a pessoa jurídica tenha de"
        "\nproceder a ajustes da contribuição apurada no"
        "\nperíodo,"
        "\ndecorrentes da legislação tributária da contribuição, de estorno ou"
        "\nde outras situações."
    )
    efdreinf01_infoProc = fields.One2many(
        "efdreinf.01.infoproc",
        "efdreinf01_infoProc_tipoCod_id",
        string="Informações de processos relacionados a Suspensão da CPRB"
    )

# Copyright 2019 Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).
# Generated Wed Mar 27 03:42:50 2019 by generateDS.py(Akretion's branch).
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
    _concrete_rec_name = 'efdreinf_evtComProd'

    efdreinf01_evtComProd = fields.Many2one(
        "efdreinf.01.evtcomprod",
        string="evtComProd",
        xsd_required=True)


class EvtComProd(spec_models.AbstractSpecMixin):
    "Evento Comercialização da ProduçãoIdentificação única do evento."
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'efdreinf.01.evtcomprod'
    _generateds_type = 'evtComProdType'
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
    efdreinf01_infoComProd = fields.Many2one(
        "efdreinf.01.infocomprod",
        string="Informação da Comercialização de Produção",
        xsd_required=True)


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
    """Registro que identifica o estabelecimento que comercializou a
    produção"""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'efdreinf.01.ideestab'
    _generateds_type = 'ideEstabType'
    _concrete_rec_name = 'efdreinf_tpInscEstab'

    efdreinf01_nrInscEstab = fields.Char(
        string="nrInscEstab",
        xsd_required=True,
        help="Informar o número de inscrição do estabelecimento do"
        "\ncontribuinte declarante, de acordo com"
        "\no tipo de inscrição indicado no campo {tpInscEstab}.")
    efdreinf01_vlrRecBrutaTotal = fields.Char(
        string="vlrRecBrutaTotal",
        xsd_required=True)
    efdreinf01_vlrCPApur = fields.Char(
        string="vlrCPApur", xsd_required=True)
    efdreinf01_vlrRatApur = fields.Char(
        string="vlrRatApur",
        xsd_required=True)
    efdreinf01_vlrSenarApur = fields.Char(
        string="vlrSenarApur",
        xsd_required=True)
    efdreinf01_vlrCPSuspTotal = fields.Char(
        string="vlrCPSuspTotal")
    efdreinf01_vlrRatSuspTotal = fields.Char(
        string="vlrRatSuspTotal")
    efdreinf01_vlrSenarSuspTotal = fields.Char(
        string="vlrSenarSuspTotal")
    efdreinf01_tipoCom = fields.One2many(
        "efdreinf.01.tipocom",
        "efdreinf01_tipoCom_ideEstab_id",
        string="tipoCom", xsd_required=True,
        help="Registro que apresenta o valor total da Receita Bruta por"
        "\n'tipo' de comercialização."
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


class InfoComProd(spec_models.AbstractSpecMixin):
    "Informação da Comercialização de Produção"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'efdreinf.01.infocomprod'
    _generateds_type = 'infoComProdType'
    _concrete_rec_name = 'efdreinf_ideEstab'

    efdreinf01_ideEstab = fields.Many2one(
        "efdreinf.01.ideestab",
        string="ideEstab", xsd_required=True,
        help="Registro que identifica o estabelecimento que comercializou a"
        "\nprodução")


class InfoProc(spec_models.AbstractSpecMixin):
    """Informações de processos administrativos/judiciais com decisão/sentença
    favorável ao contribuinte"""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'efdreinf.01.infoproc'
    _generateds_type = 'infoProcType'
    _concrete_rec_name = 'efdreinf_tpProc'

    efdreinf01_infoProc_tipoCom_id = fields.Many2one(
        "efdreinf.01.tipocom")
    efdreinf01_nrProc = fields.Char(
        string="nrProc", xsd_required=True)
    efdreinf01_codSusp = fields.Char(
        string="codSusp")
    efdreinf01_vlrCPSusp = fields.Char(
        string="vlrCPSusp")
    efdreinf01_vlrRatSusp = fields.Char(
        string="vlrRatSusp")
    efdreinf01_vlrSenarSusp = fields.Char(
        string="vlrSenarSusp")


class TipoCom(spec_models.AbstractSpecMixin):
    """Registro que apresenta o valor total da Receita Bruta por "tipo" de
    comercialização."""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'efdreinf.01.tipocom'
    _generateds_type = 'tipoComType'
    _concrete_rec_name = 'efdreinf_indCom'

    efdreinf01_tipoCom_ideEstab_id = fields.Many2one(
        "efdreinf.01.ideestab")
    efdreinf01_vlrRecBruta = fields.Char(
        string="vlrRecBruta",
        xsd_required=True)
    efdreinf01_infoProc = fields.One2many(
        "efdreinf.01.infoproc",
        "efdreinf01_infoProc_tipoCom_id",
        string="infoProc",
        help="Informações de processos administrativos/judiciais com"
        "\ndecisão/sentença favorável ao contribuinte"
    )

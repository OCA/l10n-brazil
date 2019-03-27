# Copyright 2019 Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).
# Generated Wed Mar 27 03:42:55 2019 by generateDS.py(Akretion's branch).
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
    _concrete_rec_name = 'efdreinf_evtServTom'

    efdreinf01_evtServTom = fields.Many2one(
        "efdreinf.01.evtservtom",
        string="evtServTom",
        xsd_required=True)


class EvtServTom(spec_models.AbstractSpecMixin):
    """Evento Serviços Tomados - Cessão de Mão de Obra ou
    EmpreitadaIdentificação única do evento."""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'efdreinf.01.evtservtom'
    _generateds_type = 'evtServTomType'
    _concrete_rec_name = 'efdreinf_id'

    efdreinf01_id = fields.Char(
        string="id", xsd_required=True)
    efdreinf01_ideEvento = fields.Many2one(
        "efdreinf.01.ideevento",
        string="Informações de identificação do evento",
        xsd_required=True)
    efdreinf01_ideContri = fields.Many2one(
        "efdreinf.01.idecontri",
        string="ideContri", xsd_required=True)
    efdreinf01_infoServTom = fields.Many2one(
        "efdreinf.01.infoservtom",
        string="Serviços Tomados",
        xsd_required=True,
        help="Serviços Tomados - Cessão de Mão de Obra ou Empreitada")


class IdeContri(spec_models.AbstractSpecMixin):
    _description = 'idecontri'
    _name = 'efdreinf.01.idecontri'
    _generateds_type = 'ideContriType'
    _concrete_rec_name = 'efdreinf_tpInsc'

    efdreinf01_nrInsc = fields.Char(
        string="nrInsc", xsd_required=True,
        help="Informar o número de inscrição do contribuinte de acordo com"
        "\no tipo de inscrição indicado no campo {tpInsc}."
        "\nSe for um CNPJ deve ser informada apenas a Raiz/Base de oito"
        "\nposições,"
        "\nexceto se natureza jurídica de administração pública direta federal"
        "\n([101-5], [104-0], [107-4], [116-3],"
        "\nsituação em que o campo deve ser preenchido com o CNPJ completo (14"
        "\nposições).")


class IdeEstabObra(spec_models.AbstractSpecMixin):
    "Identificação do Estabelecimento/obra contratante dos Serviços"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'efdreinf.01.ideestabobra'
    _generateds_type = 'ideEstabObraType'
    _concrete_rec_name = 'efdreinf_tpInscEstab'

    efdreinf01_nrInscEstab = fields.Char(
        string="nrInscEstab",
        xsd_required=True)
    efdreinf01_idePrestServ = fields.Many2one(
        "efdreinf.01.ideprestserv",
        string="idePrestServ",
        xsd_required=True,
        help="Identificação do prestador de serviços mediante cessão de mão"
        "\nde obra ou empreitada.")


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


class IdePrestServ(spec_models.AbstractSpecMixin):
    """Identificação do prestador de serviços mediante cessão de mão de obra ou
    empreitada."""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'efdreinf.01.ideprestserv'
    _generateds_type = 'idePrestServType'
    _concrete_rec_name = 'efdreinf_cnpjPrestador'

    efdreinf01_cnpjPrestador = fields.Char(
        string="cnpjPrestador",
        xsd_required=True)
    efdreinf01_vlrTotalBruto = fields.Char(
        string="vlrTotalBruto",
        xsd_required=True)
    efdreinf01_vlrTotalBaseRet = fields.Char(
        string="vlrTotalBaseRet",
        xsd_required=True)
    efdreinf01_vlrTotalRetPrinc = fields.Char(
        string="vlrTotalRetPrinc",
        xsd_required=True)
    efdreinf01_vlrTotalRetAdic = fields.Char(
        string="vlrTotalRetAdic")
    efdreinf01_vlrTotalNRetPrinc = fields.Char(
        string="vlrTotalNRetPrinc")
    efdreinf01_vlrTotalNRetAdic = fields.Char(
        string="vlrTotalNRetAdic")
    efdreinf01_nfs = fields.One2many(
        "efdreinf.01.nfs",
        "efdreinf01_nfs_idePrestServ_id",
        string="nfs", xsd_required=True
    )
    efdreinf01_infoProcRetPr = fields.One2many(
        "efdreinf.01.infoprocretpr",
        "efdreinf01_infoProcRetPr_idePrestServ_id",
        string="infoProcRetPr"
    )
    efdreinf01_infoProcRetAd = fields.One2many(
        "efdreinf.01.infoprocretad",
        "efdreinf01_infoProcRetAd_idePrestServ_id",
        string="infoProcRetAd"
    )


class InfoProcRetAd(spec_models.AbstractSpecMixin):
    """Informações de processos relacionados a não retenção de contribuição
    previdenciária adicional"""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'efdreinf.01.infoprocretad'
    _generateds_type = 'infoProcRetAdType'
    _concrete_rec_name = 'efdreinf_tpProcRetAdic'

    efdreinf01_infoProcRetAd_idePrestServ_id = fields.Many2one(
        "efdreinf.01.ideprestserv")
    efdreinf01_nrProcRetAdic = fields.Char(
        string="nrProcRetAdic",
        xsd_required=True)
    efdreinf01_codSuspAdic = fields.Char(
        string="codSuspAdic")
    efdreinf01_valorAdic = fields.Char(
        string="valorAdic", xsd_required=True)


class InfoProcRetPr(spec_models.AbstractSpecMixin):
    """Informações de processos relacionados a não retenção de contribuição
    previdenciária"""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'efdreinf.01.infoprocretpr'
    _generateds_type = 'infoProcRetPrType'
    _concrete_rec_name = 'efdreinf_tpProcRetPrinc'

    efdreinf01_infoProcRetPr_idePrestServ_id = fields.Many2one(
        "efdreinf.01.ideprestserv")
    efdreinf01_nrProcRetPrinc = fields.Char(
        string="nrProcRetPrinc",
        xsd_required=True)
    efdreinf01_codSuspPrinc = fields.Char(
        string="codSuspPrinc")
    efdreinf01_valorPrinc = fields.Char(
        string="valorPrinc",
        xsd_required=True)


class InfoServTom(spec_models.AbstractSpecMixin):
    "Serviços Tomados - Cessão de Mão de Obra ou Empreitada"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'efdreinf.01.infoservtom'
    _generateds_type = 'infoServTomType'
    _concrete_rec_name = 'efdreinf_ideEstabObra'

    efdreinf01_ideEstabObra = fields.Many2one(
        "efdreinf.01.ideestabobra",
        string="ideEstabObra",
        xsd_required=True,
        help="Identificação do Estabelecimento/obra contratante dos"
        "\nServiços")


class InfoTpServ(spec_models.AbstractSpecMixin):
    "Informações sobre os tipos de Serviços constantes da Nota Fiscal"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'efdreinf.01.infotpserv'
    _generateds_type = 'infoTpServType'
    _concrete_rec_name = 'efdreinf_tpServico'

    efdreinf01_infoTpServ_nfs_id = fields.Many2one(
        "efdreinf.01.nfs")
    efdreinf01_tpServico = fields.Char(
        string="tpServico", xsd_required=True)
    efdreinf01_vlrBaseRet = fields.Char(
        string="vlrBaseRet",
        xsd_required=True)
    efdreinf01_vlrRetencao = fields.Char(
        string="vlrRetencao",
        xsd_required=True)
    efdreinf01_vlrRetSub = fields.Char(
        string="vlrRetSub")
    efdreinf01_vlrNRetPrinc = fields.Char(
        string="vlrNRetPrinc")
    efdreinf01_vlrServicos15 = fields.Char(
        string="vlrServicos15")
    efdreinf01_vlrServicos20 = fields.Char(
        string="vlrServicos20")
    efdreinf01_vlrServicos25 = fields.Char(
        string="vlrServicos25")
    efdreinf01_vlrAdicional = fields.Char(
        string="vlrAdicional")
    efdreinf01_vlrNRetAdic = fields.Char(
        string="vlrNRetAdic")


class Nfs(spec_models.AbstractSpecMixin):
    """Detalhamento das notas fiscais de serviços prestados pela empresa
    identificada no registro superior."""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'efdreinf.01.nfs'
    _generateds_type = 'nfsType'
    _concrete_rec_name = 'efdreinf_serie'

    efdreinf01_nfs_idePrestServ_id = fields.Many2one(
        "efdreinf.01.ideprestserv")
    efdreinf01_serie = fields.Char(
        string="serie", xsd_required=True)
    efdreinf01_numDocto = fields.Char(
        string="numDocto", xsd_required=True)
    efdreinf01_dtEmissaoNF = fields.Date(
        string="dtEmissaoNF",
        xsd_required=True)
    efdreinf01_vlrBruto = fields.Char(
        string="vlrBruto", xsd_required=True)
    efdreinf01_obs = fields.Char(
        string="obs")
    efdreinf01_infoTpServ = fields.One2many(
        "efdreinf.01.infotpserv",
        "efdreinf01_infoTpServ_nfs_id",
        string="infoTpServ",
        xsd_required=True
    )

# Copyright 2019 Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).
# Generated Fri Mar 29 03:16:28 2019 by generateDS.py(Akretion's branch).
# Python 3.6.7 (default, Oct 22 2018, 11:32:17)  [GCC 8.2.0]
#
import textwrap
from odoo import fields
from .. import spec_models


class TIdeEveFopagMensal(spec_models.AbstractSpecMixin):
    "Identificação do Evento Periódico"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtcomprodl.tideevefopagmensal'
    _generateds_type = 'TIdeEveFopagMensal'
    _concrete_rec_name = 'esoc_indRetif'

    esoc02_indRetif = fields.Boolean(
        string="indRetif", xsd_required=True)
    esoc02_nrRecibo = fields.Char(
        string="nrRecibo")
    esoc02_indApuracao = fields.Boolean(
        string="indApuracao", xsd_required=True)
    esoc02_perApur = fields.Char(
        string="perApur", xsd_required=True)
    esoc02_tpAmb = fields.Boolean(
        string="tpAmb", xsd_required=True)
    esoc02_procEmi = fields.Boolean(
        string="procEmi", xsd_required=True)
    esoc02_verProc = fields.Char(
        string="verProc", xsd_required=True)


class ESocial(spec_models.AbstractSpecMixin):
    _description = 'esocial'
    _name = 'esoc.02.evtcomprodl.esocial'
    _generateds_type = 'eSocial'
    _concrete_rec_name = 'esoc_evtComProd'

    esoc02_evtComProd = fields.Many2one(
        "esoc.02.evtcomprodl.evtcomprod",
        string="evtComProd", xsd_required=True)


class EvtComProd(spec_models.AbstractSpecMixin):
    "Evento Comercialização da Produção Rural Pessoa Física"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtcomprodl.evtcomprod'
    _generateds_type = 'evtComProdType'
    _concrete_rec_name = 'esoc_Id'

    esoc02_Id = fields.Char(
        string="Id", xsd_required=True)
    esoc02_ideEvento = fields.Many2one(
        "esoc.02.evtcomprodl.tideevefopagmensal",
        string="Informações de identificação do evento",
        xsd_required=True)
    esoc02_ideEmpregador = fields.Many2one(
        "esoc.02.evtcomprodl.ideempregador",
        string="Informações de identificação do empregador",
        xsd_required=True)
    esoc02_infoComProd = fields.Many2one(
        "esoc.02.evtcomprodl.infocomprod",
        string="Informação da Comercialização de Produção",
        xsd_required=True)


class IdeAdquir(spec_models.AbstractSpecMixin):
    "Identificação dos Adquirentes da Produção"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtcomprodl.ideadquir'
    _generateds_type = 'ideAdquirType'
    _concrete_rec_name = 'esoc_tpInsc'

    esoc02_ideAdquir_tpComerc_id = fields.Many2one(
        "esoc.02.evtcomprodl.tpcomerc")
    esoc02_tpInsc = fields.Boolean(
        string="tpInsc", xsd_required=True)
    esoc02_nrInsc = fields.Char(
        string="nrInsc", xsd_required=True)
    esoc02_vrComerc = fields.Monetary(
        string="vrComerc", xsd_required=True)
    esoc02_nfs = fields.One2many(
        "esoc.02.evtcomprodl.nfs",
        "esoc02_nfs_ideAdquir_id",
        string="Notas Fiscais da aquisição de produção"
    )


class IdeEmpregador(spec_models.AbstractSpecMixin):
    "Informações de identificação do empregador"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtcomprodl.ideempregador'
    _generateds_type = 'ideEmpregadorType'
    _concrete_rec_name = 'esoc_tpInsc'

    esoc02_tpInsc = fields.Boolean(
        string="tpInsc", xsd_required=True)
    esoc02_nrInsc = fields.Char(
        string="nrInsc", xsd_required=True)


class IdeEstabel(spec_models.AbstractSpecMixin):
    "Identificação do estabelecimento que comercializou a produção"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtcomprodl.ideestabel'
    _generateds_type = 'ideEstabelType'
    _concrete_rec_name = 'esoc_nrInscEstabRural'

    esoc02_nrInscEstabRural = fields.Char(
        string="nrInscEstabRural",
        xsd_required=True)
    esoc02_tpComerc = fields.One2many(
        "esoc.02.evtcomprodl.tpcomerc",
        "esoc02_tpComerc_ideEstabel_id",
        string="tpComerc", xsd_required=True,
        help="Registro que apresenta o valor total da comercialização por"
        "\n'tipo' de comercialização"
    )


class InfoComProd(spec_models.AbstractSpecMixin):
    "Informação da Comercialização de Produção"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtcomprodl.infocomprod'
    _generateds_type = 'infoComProdType'
    _concrete_rec_name = 'esoc_ideEstabel'

    esoc02_ideEstabel = fields.Many2one(
        "esoc.02.evtcomprodl.ideestabel",
        string="ideEstabel", xsd_required=True,
        help="Identificação do estabelecimento que comercializou a produção")


class InfoProcJud(spec_models.AbstractSpecMixin):
    "Informação de Processo Judicial"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtcomprodl.infoprocjud'
    _generateds_type = 'infoProcJudType'
    _concrete_rec_name = 'esoc_tpProc'

    esoc02_infoProcJud_tpComerc_id = fields.Many2one(
        "esoc.02.evtcomprodl.tpcomerc")
    esoc02_tpProc = fields.Boolean(
        string="tpProc", xsd_required=True)
    esoc02_nrProc = fields.Char(
        string="nrProc", xsd_required=True)
    esoc02_codSusp = fields.Integer(
        string="codSusp", xsd_required=True)
    esoc02_vrCPSusp = fields.Monetary(
        string="vrCPSusp")
    esoc02_vrRatSusp = fields.Monetary(
        string="vrRatSusp")
    esoc02_vrSenarSusp = fields.Monetary(
        string="vrSenarSusp")


class Nfs(spec_models.AbstractSpecMixin):
    "Notas Fiscais da aquisição de produção"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtcomprodl.nfs'
    _generateds_type = 'nfsType'
    _concrete_rec_name = 'esoc_serie'

    esoc02_nfs_ideAdquir_id = fields.Many2one(
        "esoc.02.evtcomprodl.ideadquir")
    esoc02_serie = fields.Char(
        string="serie")
    esoc02_nrDocto = fields.Char(
        string="nrDocto", xsd_required=True)
    esoc02_dtEmisNF = fields.Date(
        string="dtEmisNF", xsd_required=True)
    esoc02_vlrBruto = fields.Monetary(
        string="vlrBruto", xsd_required=True)
    esoc02_vrCPDescPR = fields.Monetary(
        string="vrCPDescPR", xsd_required=True)
    esoc02_vrRatDescPR = fields.Monetary(
        string="vrRatDescPR", xsd_required=True)
    esoc02_vrSenarDesc = fields.Monetary(
        string="vrSenarDesc", xsd_required=True)


class TpComerc(spec_models.AbstractSpecMixin):
    """Registro que apresenta o valor total da comercialização por "tipo" de
    comercialização"""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtcomprodl.tpcomerc'
    _generateds_type = 'tpComercType'
    _concrete_rec_name = 'esoc_indComerc'

    esoc02_tpComerc_ideEstabel_id = fields.Many2one(
        "esoc.02.evtcomprodl.ideestabel")
    esoc02_indComerc = fields.Boolean(
        string="indComerc", xsd_required=True)
    esoc02_vrTotCom = fields.Monetary(
        string="vrTotCom", xsd_required=True)
    esoc02_ideAdquir = fields.One2many(
        "esoc.02.evtcomprodl.ideadquir",
        "esoc02_ideAdquir_tpComerc_id",
        string="Identificação dos Adquirentes da Produção"
    )
    esoc02_infoProcJud = fields.One2many(
        "esoc.02.evtcomprodl.infoprocjud",
        "esoc02_infoProcJud_tpComerc_id",
        string="Informação de Processo Judicial"
    )

# Copyright 2019 Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).
# Generated Fri Mar 29 03:16:23 2019 by generateDS.py(Akretion's branch).
# Python 3.6.7 (default, Oct 22 2018, 11:32:17)  [GCC 8.2.0]
#
import textwrap
from odoo import fields
from .. import spec_models


class TEmpregador(spec_models.AbstractSpecMixin):
    _description = 'tempregador'
    _name = 'esoc.02.evtaqprodli.tempregador'
    _generateds_type = 'TEmpregador'
    _concrete_rec_name = 'esoc_tpInsc'

    esoc02_tpInsc = fields.Boolean(
        string="tpInsc", xsd_required=True)
    esoc02_nrInsc = fields.Char(
        string="nrInsc", xsd_required=True)


class TIdeEveFopagMensal(spec_models.AbstractSpecMixin):
    "Identificação do Evento Periódico"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtaqprodli.tideevefopagmensal'
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
    _name = 'esoc.02.evtaqprodli.esocial'
    _generateds_type = 'eSocial'
    _concrete_rec_name = 'esoc_evtAqProd'

    esoc02_evtAqProd = fields.Many2one(
        "esoc.02.evtaqprodli.evtaqprod",
        string="evtAqProd", xsd_required=True)


class EvtAqProd(spec_models.AbstractSpecMixin):
    "Evento Aquisição de Produção"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtaqprodli.evtaqprod'
    _generateds_type = 'evtAqProdType'
    _concrete_rec_name = 'esoc_Id'

    esoc02_Id = fields.Char(
        string="Id", xsd_required=True)
    esoc02_ideEvento = fields.Many2one(
        "esoc.02.evtaqprodli.tideevefopagmensal",
        string="Informações de identificação do evento",
        xsd_required=True)
    esoc02_ideEmpregador = fields.Many2one(
        "esoc.02.evtaqprodli.tempregador",
        string="Informações de identificação do empregador",
        xsd_required=True)
    esoc02_infoAquisProd = fields.Many2one(
        "esoc.02.evtaqprodli.infoaquisprod",
        string="Informação da Aquisição de Produção",
        xsd_required=True)


class IdeEstabAdquir(spec_models.AbstractSpecMixin):
    "Identificação do estabelecimento adquirente da produção"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtaqprodli.ideestabadquir'
    _generateds_type = 'ideEstabAdquirType'
    _concrete_rec_name = 'esoc_tpInscAdq'

    esoc02_tpInscAdq = fields.Boolean(
        string="tpInscAdq", xsd_required=True)
    esoc02_nrInscAdq = fields.Char(
        string="nrInscAdq", xsd_required=True)
    esoc02_tpAquis = fields.One2many(
        "esoc.02.evtaqprodli.tpaquis",
        "esoc02_tpAquis_ideEstabAdquir_id",
        string="Aquisição de produção",
        xsd_required=True
    )


class IdeProdutor(spec_models.AbstractSpecMixin):
    "Identificação dos produtores rurais"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtaqprodli.ideprodutor'
    _generateds_type = 'ideProdutorType'
    _concrete_rec_name = 'esoc_tpInscProd'

    esoc02_ideProdutor_tpAquis_id = fields.Many2one(
        "esoc.02.evtaqprodli.tpaquis")
    esoc02_tpInscProd = fields.Boolean(
        string="tpInscProd", xsd_required=True)
    esoc02_nrInscProd = fields.Char(
        string="nrInscProd", xsd_required=True)
    esoc02_vlrBruto = fields.Monetary(
        string="vlrBruto", xsd_required=True)
    esoc02_vrCPDescPR = fields.Monetary(
        string="vrCPDescPR", xsd_required=True)
    esoc02_vrRatDescPR = fields.Monetary(
        string="vrRatDescPR", xsd_required=True)
    esoc02_vrSenarDesc = fields.Monetary(
        string="vrSenarDesc", xsd_required=True)
    esoc02_indOpcCP = fields.Boolean(
        string="indOpcCP", xsd_required=True)
    esoc02_nfs = fields.One2many(
        "esoc.02.evtaqprodli.nfs",
        "esoc02_nfs_ideProdutor_id",
        string="Notas Fiscais da aquisição de produção"
    )
    esoc02_infoProcJud = fields.One2many(
        "esoc.02.evtaqprodli.infoprocjud",
        "esoc02_infoProcJud_ideProdutor_id",
        string="Informação de Processo Judicial do produtor"
    )


class InfoAquisProd(spec_models.AbstractSpecMixin):
    "Informação da Aquisição de Produção"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtaqprodli.infoaquisprod'
    _generateds_type = 'infoAquisProdType'
    _concrete_rec_name = 'esoc_ideEstabAdquir'

    esoc02_ideEstabAdquir = fields.Many2one(
        "esoc.02.evtaqprodli.ideestabadquir",
        string="Identificação do estabelecimento adquirente da produção",
        xsd_required=True)


class InfoProcJ(spec_models.AbstractSpecMixin):
    "Informações de Processo Judicial comum a todos os produtores"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtaqprodli.infoprocj'
    _generateds_type = 'infoProcJType'
    _concrete_rec_name = 'esoc_nrProcJud'

    esoc02_infoProcJ_tpAquis_id = fields.Many2one(
        "esoc.02.evtaqprodli.tpaquis")
    esoc02_nrProcJud = fields.Char(
        string="nrProcJud", xsd_required=True)
    esoc02_codSusp = fields.Integer(
        string="codSusp", xsd_required=True)
    esoc02_vrCPNRet = fields.Monetary(
        string="vrCPNRet", xsd_required=True)
    esoc02_vrRatNRet = fields.Monetary(
        string="vrRatNRet", xsd_required=True)
    esoc02_vrSenarNRet = fields.Monetary(
        string="vrSenarNRet", xsd_required=True)


class InfoProcJud(spec_models.AbstractSpecMixin):
    "Informação de Processo Judicial do produtor"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtaqprodli.infoprocjud'
    _generateds_type = 'infoProcJudType'
    _concrete_rec_name = 'esoc_nrProcJud'

    esoc02_infoProcJud_ideProdutor_id = fields.Many2one(
        "esoc.02.evtaqprodli.ideprodutor")
    esoc02_nrProcJud = fields.Char(
        string="nrProcJud", xsd_required=True)
    esoc02_codSusp = fields.Integer(
        string="codSusp", xsd_required=True)
    esoc02_vrCPNRet = fields.Monetary(
        string="vrCPNRet", xsd_required=True)
    esoc02_vrRatNRet = fields.Monetary(
        string="vrRatNRet", xsd_required=True)
    esoc02_vrSenarNRet = fields.Monetary(
        string="vrSenarNRet", xsd_required=True)


class Nfs(spec_models.AbstractSpecMixin):
    "Notas Fiscais da aquisição de produção"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtaqprodli.nfs'
    _generateds_type = 'nfsType'
    _concrete_rec_name = 'esoc_serie'

    esoc02_nfs_ideProdutor_id = fields.Many2one(
        "esoc.02.evtaqprodli.ideprodutor")
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


class TpAquis(spec_models.AbstractSpecMixin):
    "Aquisição de produção"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtaqprodli.tpaquis'
    _generateds_type = 'tpAquisType'
    _concrete_rec_name = 'esoc_indAquis'

    esoc02_tpAquis_ideEstabAdquir_id = fields.Many2one(
        "esoc.02.evtaqprodli.ideestabadquir")
    esoc02_indAquis = fields.Boolean(
        string="indAquis", xsd_required=True)
    esoc02_vlrTotAquis = fields.Monetary(
        string="vlrTotAquis", xsd_required=True)
    esoc02_ideProdutor = fields.One2many(
        "esoc.02.evtaqprodli.ideprodutor",
        "esoc02_ideProdutor_tpAquis_id",
        string="Identificação dos produtores rurais",
        xsd_required=True
    )
    esoc02_infoProcJ = fields.One2many(
        "esoc.02.evtaqprodli.infoprocj",
        "esoc02_infoProcJ_tpAquis_id",
        string="infoProcJ",
        help="Informações de Processo Judicial comum a todos os produtores"
    )

# Copyright 2019 Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).
# Generated Fri Mar 29 03:16:39 2019 by generateDS.py(Akretion's branch).
# Python 3.6.7 (default, Oct 22 2018, 11:32:17)  [GCC 8.2.0]
#
import textwrap
from odoo import fields
from .. import spec_models


class TEmpregador(spec_models.AbstractSpecMixin):
    _description = 'tempregador'
    _name = 'esoc.02.evtpgtoslib.tempregador'
    _generateds_type = 'TEmpregador'
    _concrete_rec_name = 'esoc_tpInsc'

    esoc02_tpInsc = fields.Boolean(
        string="tpInsc", xsd_required=True)
    esoc02_nrInsc = fields.Char(
        string="nrInsc", xsd_required=True)


class TIdeEveFopagMensal(spec_models.AbstractSpecMixin):
    "Identificação do Evento Periódico"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtpgtoslib.tideevefopagmensal'
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


class TNaoResid(spec_models.AbstractSpecMixin):
    "Endereço no Exterior - Fiscal"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtpgtoslib.tnaoresid'
    _generateds_type = 'TNaoResid'
    _concrete_rec_name = 'esoc_idePais'

    esoc02_idePais = fields.Many2one(
        "esoc.02.evtpgtoslib.idepais",
        string="Identificação do País onde foi efetuado o pagamento",
        xsd_required=True)
    esoc02_endExt = fields.Many2one(
        "esoc.02.evtpgtoslib.endext",
        string="Informações complementares de endereço do beneficiário",
        xsd_required=True)


class TPensaoAlim(spec_models.AbstractSpecMixin):
    _description = 'tpensaoalim'
    _name = 'esoc.02.evtpgtoslib.tpensaoalim'
    _generateds_type = 'TPensaoAlim'
    _concrete_rec_name = 'esoc_cpfBenef'

    esoc02_penAlim_detRubrFer_id = fields.Many2one(
        "esoc.02.evtpgtoslib.detrubrfer")
    esoc02_penAlim_retPgtoTot_id = fields.Many2one(
        "esoc.02.evtpgtoslib.retpgtotot")
    esoc02_cpfBenef = fields.Char(
        string="cpfBenef", xsd_required=True)
    esoc02_dtNasctoBenef = fields.Date(
        string="dtNasctoBenef")
    esoc02_nmBenefic = fields.Char(
        string="nmBenefic", xsd_required=True)
    esoc02_vlrPensao = fields.Monetary(
        string="vlrPensao", xsd_required=True)


class TRubrCaixa(spec_models.AbstractSpecMixin):
    "Rubricas de pagamento"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtpgtoslib.trubrcaixa'
    _generateds_type = 'TRubrCaixa'
    _concrete_rec_name = 'esoc_codRubr'

    esoc02_retPgtoTot_detPgtoBenPr_id = fields.Many2one(
        "esoc.02.evtpgtoslib.detpgtobenpr")
    esoc02_codRubr = fields.Char(
        string="codRubr", xsd_required=True)
    esoc02_ideTabRubr = fields.Char(
        string="ideTabRubr", xsd_required=True)
    esoc02_qtdRubr = fields.Monetary(
        string="qtdRubr")
    esoc02_fatorRubr = fields.Monetary(
        string="fatorRubr")
    esoc02_vrUnit = fields.Monetary(
        string="vrUnit")
    esoc02_vrRubr = fields.Monetary(
        string="vrRubr", xsd_required=True)


class Deps(spec_models.AbstractSpecMixin):
    "Informações de dependentes do beneficiário"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtpgtoslib.deps'
    _generateds_type = 'depsType'
    _concrete_rec_name = 'esoc_vrDedDep'

    esoc02_vrDedDep = fields.Monetary(
        string="vrDedDep", xsd_required=True)


class DetPgtoAnt(spec_models.AbstractSpecMixin):
    """Pagamento relativo a competências anteriores ao início de
    obrigatoriedade dos eventos periódicos"""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtpgtoslib.detpgtoant'
    _generateds_type = 'detPgtoAntType'
    _concrete_rec_name = 'esoc_codCateg'

    esoc02_detPgtoAnt_infoPgto_id = fields.Many2one(
        "esoc.02.evtpgtoslib.infopgto")
    esoc02_codCateg = fields.Integer(
        string="codCateg", xsd_required=True)
    esoc02_infoPgtoAnt = fields.One2many(
        "esoc.02.evtpgtoslib.infopgtoant",
        "esoc02_infoPgtoAnt_detPgtoAnt_id",
        string="Detalhamento do pagamento",
        xsd_required=True
    )


class DetPgtoBenPr(spec_models.AbstractSpecMixin):
    "Detalhamento de pagamentos relativos a benefícios previdenciários"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtpgtoslib.detpgtobenpr'
    _generateds_type = 'detPgtoBenPrType'
    _concrete_rec_name = 'esoc_perRef'

    esoc02_perRef = fields.Char(
        string="perRef", xsd_required=True)
    esoc02_ideDmDev = fields.Char(
        string="ideDmDev", xsd_required=True)
    esoc02_indPgtoTt = fields.Char(
        string="indPgtoTt", xsd_required=True)
    esoc02_vrLiq = fields.Monetary(
        string="vrLiq", xsd_required=True)
    esoc02_retPgtoTot = fields.One2many(
        "esoc.02.evtpgtoslib.trubrcaixa",
        "esoc02_retPgtoTot_detPgtoBenPr_id",
        string="Retenções efetuadas no ato do pagamento"
    )
    esoc02_infoPgtoParc = fields.One2many(
        "esoc.02.evtpgtoslib.infopgtoparc11",
        "esoc02_infoPgtoParc_detPgtoBenPr_id",
        string="infoPgtoParc",
        help="Informações complementares relacionadas ao pagamento parcial"
    )


class DetPgtoFer(spec_models.AbstractSpecMixin):
    "Detalhamento dos pagamentos de férias"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtpgtoslib.detpgtofer'
    _generateds_type = 'detPgtoFerType'
    _concrete_rec_name = 'esoc_codCateg'

    esoc02_detPgtoFer_infoPgto_id = fields.Many2one(
        "esoc.02.evtpgtoslib.infopgto")
    esoc02_codCateg = fields.Integer(
        string="codCateg", xsd_required=True)
    esoc02_matricula = fields.Char(
        string="matricula")
    esoc02_dtIniGoz = fields.Date(
        string="dtIniGoz", xsd_required=True)
    esoc02_qtDias = fields.Boolean(
        string="qtDias", xsd_required=True)
    esoc02_vrLiq = fields.Monetary(
        string="vrLiq", xsd_required=True)
    esoc02_detRubrFer = fields.One2many(
        "esoc.02.evtpgtoslib.detrubrfer",
        "esoc02_detRubrFer_detPgtoFer_id",
        string="Detalhamento das rubricas",
        xsd_required=True
    )


class DetPgtoFl(spec_models.AbstractSpecMixin):
    "Detalhamento dos pagamentos efetuados apurados em S-1200 ou S-1202"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtpgtoslib.detpgtofl'
    _generateds_type = 'detPgtoFlType'
    _concrete_rec_name = 'esoc_perRef'

    esoc02_detPgtoFl_infoPgto_id = fields.Many2one(
        "esoc.02.evtpgtoslib.infopgto")
    esoc02_perRef = fields.Char(
        string="perRef")
    esoc02_ideDmDev = fields.Char(
        string="ideDmDev", xsd_required=True)
    esoc02_indPgtoTt = fields.Char(
        string="indPgtoTt", xsd_required=True)
    esoc02_vrLiq = fields.Monetary(
        string="vrLiq", xsd_required=True)
    esoc02_nrRecArq = fields.Char(
        string="nrRecArq")
    esoc02_retPgtoTot = fields.One2many(
        "esoc.02.evtpgtoslib.retpgtotot",
        "esoc02_retPgtoTot_detPgtoFl_id",
        string="Retenções efetuadas no ato do pagamento"
    )
    esoc02_infoPgtoParc = fields.One2many(
        "esoc.02.evtpgtoslib.infopgtoparc",
        "esoc02_infoPgtoParc_detPgtoFl_id",
        string="infoPgtoParc",
        help="Informações complementares relacionadas ao pagamento parcial"
    )


class DetRubrFer(spec_models.AbstractSpecMixin):
    "Detalhamento das rubricas"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtpgtoslib.detrubrfer'
    _generateds_type = 'detRubrFerType'
    _concrete_rec_name = 'esoc_codRubr'

    esoc02_detRubrFer_detPgtoFer_id = fields.Many2one(
        "esoc.02.evtpgtoslib.detpgtofer")
    esoc02_codRubr = fields.Char(
        string="codRubr", xsd_required=True)
    esoc02_ideTabRubr = fields.Char(
        string="ideTabRubr", xsd_required=True)
    esoc02_qtdRubr = fields.Monetary(
        string="qtdRubr")
    esoc02_fatorRubr = fields.Monetary(
        string="fatorRubr")
    esoc02_vrUnit = fields.Monetary(
        string="vrUnit")
    esoc02_vrRubr = fields.Monetary(
        string="vrRubr", xsd_required=True)
    esoc02_penAlim = fields.One2many(
        "esoc.02.evtpgtoslib.tpensaoalim",
        "esoc02_penAlim_detRubrFer_id",
        string="penAlim"
    )


class ESocial(spec_models.AbstractSpecMixin):
    _description = 'esocial'
    _name = 'esoc.02.evtpgtoslib.esocial'
    _generateds_type = 'eSocial'
    _concrete_rec_name = 'esoc_evtPgtos'

    esoc02_evtPgtos = fields.Many2one(
        "esoc.02.evtpgtoslib.evtpgtos",
        string="evtPgtos", xsd_required=True)


class EndExt(spec_models.AbstractSpecMixin):
    "Informações complementares de endereço do beneficiário"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtpgtoslib.endext'
    _generateds_type = 'endExtType'
    _concrete_rec_name = 'esoc_dscLograd'

    esoc02_dscLograd = fields.Char(
        string="dscLograd", xsd_required=True)
    esoc02_nrLograd = fields.Char(
        string="nrLograd")
    esoc02_complem = fields.Char(
        string="complem")
    esoc02_bairro = fields.Char(
        string="bairro")
    esoc02_nmCid = fields.Char(
        string="nmCid", xsd_required=True)
    esoc02_codPostal = fields.Char(
        string="codPostal")


class EvtPgtos(spec_models.AbstractSpecMixin):
    "Evento Pagtos Efetuados"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtpgtoslib.evtpgtos'
    _generateds_type = 'evtPgtosType'
    _concrete_rec_name = 'esoc_Id'

    esoc02_Id = fields.Char(
        string="Id", xsd_required=True)
    esoc02_ideEvento = fields.Many2one(
        "esoc.02.evtpgtoslib.tideevefopagmensal",
        string="Informações de identificação do evento",
        xsd_required=True)
    esoc02_ideEmpregador = fields.Many2one(
        "esoc.02.evtpgtoslib.tempregador",
        string="Informações de identificação do empregador",
        xsd_required=True)
    esoc02_ideBenef = fields.Many2one(
        "esoc.02.evtpgtoslib.idebenef",
        string="Identificação do beneficiário do pagamento",
        xsd_required=True)


class IdeBenef(spec_models.AbstractSpecMixin):
    "Identificação do beneficiário do pagamento"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtpgtoslib.idebenef'
    _generateds_type = 'ideBenefType'
    _concrete_rec_name = 'esoc_cpfBenef'

    esoc02_cpfBenef = fields.Char(
        string="cpfBenef", xsd_required=True)
    esoc02_deps = fields.Many2one(
        "esoc.02.evtpgtoslib.deps",
        string="Informações de dependentes do beneficiário")
    esoc02_infoPgto = fields.One2many(
        "esoc.02.evtpgtoslib.infopgto",
        "esoc02_infoPgto_ideBenef_id",
        string="Informações dos pagamentos efetuados",
        xsd_required=True
    )


class IdePais(spec_models.AbstractSpecMixin):
    "Identificação do País onde foi efetuado o pagamento"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtpgtoslib.idepais'
    _generateds_type = 'idePaisType'
    _concrete_rec_name = 'esoc_codPais'

    esoc02_codPais = fields.Char(
        string="codPais", xsd_required=True)
    esoc02_indNIF = fields.Boolean(
        string="indNIF", xsd_required=True)
    esoc02_nifBenef = fields.Char(
        string="nifBenef")


class InfoPgtoAnt(spec_models.AbstractSpecMixin):
    "Detalhamento do pagamento"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtpgtoslib.infopgtoant'
    _generateds_type = 'infoPgtoAntType'
    _concrete_rec_name = 'esoc_tpBcIRRF'

    esoc02_infoPgtoAnt_detPgtoAnt_id = fields.Many2one(
        "esoc.02.evtpgtoslib.detpgtoant")
    esoc02_tpBcIRRF = fields.Char(
        string="tpBcIRRF", xsd_required=True)
    esoc02_vrBcIRRF = fields.Monetary(
        string="vrBcIRRF", xsd_required=True)


class InfoPgtoParc(spec_models.AbstractSpecMixin):
    "Informações complementares relacionadas ao pagamento parcial"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtpgtoslib.infopgtoparc'
    _generateds_type = 'infoPgtoParcType'
    _concrete_rec_name = 'esoc_matricula'

    esoc02_infoPgtoParc_detPgtoFl_id = fields.Many2one(
        "esoc.02.evtpgtoslib.detpgtofl")
    esoc02_matricula = fields.Char(
        string="matricula")
    esoc02_codRubr = fields.Char(
        string="codRubr", xsd_required=True)
    esoc02_ideTabRubr = fields.Char(
        string="ideTabRubr", xsd_required=True)
    esoc02_qtdRubr = fields.Monetary(
        string="qtdRubr")
    esoc02_fatorRubr = fields.Monetary(
        string="fatorRubr")
    esoc02_vrUnit = fields.Monetary(
        string="vrUnit")
    esoc02_vrRubr = fields.Monetary(
        string="vrRubr", xsd_required=True)


class InfoPgtoParc11(spec_models.AbstractSpecMixin):
    "Informações complementares relacionadas ao pagamento parcial"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtpgtoslib.infopgtoparc11'
    _generateds_type = 'infoPgtoParcType11'
    _concrete_rec_name = 'esoc_codRubr'

    esoc02_infoPgtoParc_detPgtoBenPr_id = fields.Many2one(
        "esoc.02.evtpgtoslib.detpgtobenpr")
    esoc02_codRubr = fields.Char(
        string="codRubr", xsd_required=True)
    esoc02_ideTabRubr = fields.Char(
        string="ideTabRubr", xsd_required=True)
    esoc02_qtdRubr = fields.Monetary(
        string="qtdRubr")
    esoc02_fatorRubr = fields.Monetary(
        string="fatorRubr")
    esoc02_vrUnit = fields.Monetary(
        string="vrUnit")
    esoc02_vrRubr = fields.Monetary(
        string="vrRubr", xsd_required=True)


class InfoPgto(spec_models.AbstractSpecMixin):
    "Informações dos pagamentos efetuados"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtpgtoslib.infopgto'
    _generateds_type = 'infoPgtoType'
    _concrete_rec_name = 'esoc_dtPgto'

    esoc02_infoPgto_ideBenef_id = fields.Many2one(
        "esoc.02.evtpgtoslib.idebenef")
    esoc02_dtPgto = fields.Date(
        string="dtPgto", xsd_required=True)
    esoc02_tpPgto = fields.Boolean(
        string="tpPgto", xsd_required=True)
    esoc02_indResBr = fields.Char(
        string="indResBr", xsd_required=True)
    esoc02_detPgtoFl = fields.One2many(
        "esoc.02.evtpgtoslib.detpgtofl",
        "esoc02_detPgtoFl_infoPgto_id",
        string="Detalhamento dos pagamentos efetuados apurados em S",
        help="Detalhamento dos pagamentos efetuados apurados em S-1200 ou"
        "\nS-1202"
    )
    esoc02_detPgtoBenPr = fields.Many2one(
        "esoc.02.evtpgtoslib.detpgtobenpr",
        string="detPgtoBenPr",
        help="Detalhamento de pagamentos relativos a benefícios"
        "\nprevidenciários")
    esoc02_detPgtoFer = fields.One2many(
        "esoc.02.evtpgtoslib.detpgtofer",
        "esoc02_detPgtoFer_infoPgto_id",
        string="Detalhamento dos pagamentos de férias"
    )
    esoc02_detPgtoAnt = fields.One2many(
        "esoc.02.evtpgtoslib.detpgtoant",
        "esoc02_detPgtoAnt_infoPgto_id",
        string="detPgtoAnt",
        help="Pagamento relativo a competências anteriores ao início de"
        "\nobrigatoriedade dos eventos periódicos"
    )
    esoc02_idePgtoExt = fields.Many2one(
        "esoc.02.evtpgtoslib.tnaoresid",
        string="Informações complementares sobre pagamentos no exterior")


class RetPgtoTot(spec_models.AbstractSpecMixin):
    "Retenções efetuadas no ato do pagamento"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtpgtoslib.retpgtotot'
    _generateds_type = 'retPgtoTotType'
    _concrete_rec_name = 'esoc_codRubr'

    esoc02_retPgtoTot_detPgtoFl_id = fields.Many2one(
        "esoc.02.evtpgtoslib.detpgtofl")
    esoc02_codRubr = fields.Char(
        string="codRubr", xsd_required=True)
    esoc02_ideTabRubr = fields.Char(
        string="ideTabRubr", xsd_required=True)
    esoc02_qtdRubr = fields.Monetary(
        string="qtdRubr")
    esoc02_fatorRubr = fields.Monetary(
        string="fatorRubr")
    esoc02_vrUnit = fields.Monetary(
        string="vrUnit")
    esoc02_vrRubr = fields.Monetary(
        string="vrRubr", xsd_required=True)
    esoc02_penAlim = fields.One2many(
        "esoc.02.evtpgtoslib.tpensaoalim",
        "esoc02_penAlim_retPgtoTot_id",
        string="penAlim"
    )

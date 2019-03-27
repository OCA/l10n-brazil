# Copyright 2019 Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).
# Generated Fri Mar 29 03:16:36 2019 by generateDS.py(Akretion's branch).
# Python 3.6.7 (default, Oct 22 2018, 11:32:17)  [GCC 8.2.0]
#
import textwrap
from odoo import fields
from .. import spec_models

# Sigla da UF
uf_infoEnte = [
    ("AC", "AC"),
    ("AL", "AL"),
    ("AP", "AP"),
    ("AM", "AM"),
    ("BA", "BA"),
    ("CE", "CE"),
    ("DF", "DF"),
    ("ES", "ES"),
    ("GO", "GO"),
    ("MA", "MA"),
    ("MT", "MT"),
    ("MS", "MS"),
    ("MG", "MG"),
    ("PA", "PA"),
    ("PB", "PB"),
    ("PR", "PR"),
    ("PE", "PE"),
    ("PI", "PI"),
    ("RJ", "RJ"),
    ("RN", "RN"),
    ("RS", "RS"),
    ("RO", "RO"),
    ("RR", "RR"),
    ("SC", "SC"),
    ("SP", "SP"),
    ("SE", "SE"),
    ("TO", "TO"),
]


class TEmpregador(spec_models.AbstractSpecMixin):
    _description = 'tempregador'
    _name = 'esoc.02.evtinfoempr.tempregador'
    _generateds_type = 'TEmpregador'
    _concrete_rec_name = 'esoc_tpInsc'

    esoc02_tpInsc = fields.Boolean(
        string="tpInsc", xsd_required=True)
    esoc02_nrInsc = fields.Char(
        string="nrInsc", xsd_required=True)


class TIdeCadastro(spec_models.AbstractSpecMixin):
    "Identificação de evento de cadastro/tabelas"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtinfoempr.tidecadastro'
    _generateds_type = 'TIdeCadastro'
    _concrete_rec_name = 'esoc_tpAmb'

    esoc02_tpAmb = fields.Boolean(
        string="tpAmb", xsd_required=True)
    esoc02_procEmi = fields.Boolean(
        string="procEmi", xsd_required=True)
    esoc02_verProc = fields.Char(
        string="verProc", xsd_required=True)


class TIdePeriodo(spec_models.AbstractSpecMixin):
    "Identificação do Período de Validade das Informações"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtinfoempr.tideperiodo'
    _generateds_type = 'TIdePeriodo'
    _concrete_rec_name = 'esoc_iniValid'

    esoc02_iniValid = fields.Char(
        string="iniValid", xsd_required=True)
    esoc02_fimValid = fields.Char(
        string="fimValid")


class TInfoEmpregador(spec_models.AbstractSpecMixin):
    "Informações do Empregador"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtinfoempr.tinfoempregador'
    _generateds_type = 'TInfoEmpregador'
    _concrete_rec_name = 'esoc_nmRazao'

    esoc02_nmRazao = fields.Char(
        string="nmRazao", xsd_required=True)
    esoc02_classTrib = fields.Char(
        string="classTrib", xsd_required=True)
    esoc02_natJurid = fields.Char(
        string="natJurid")
    esoc02_indCoop = fields.Boolean(
        string="indCoop")
    esoc02_indConstr = fields.Boolean(
        string="indConstr")
    esoc02_indDesFolha = fields.Boolean(
        string="indDesFolha", xsd_required=True)
    esoc02_indOpcCP = fields.Boolean(
        string="indOpcCP")
    esoc02_indOptRegEletron = fields.Boolean(
        string="indOptRegEletron",
        xsd_required=True)
    esoc02_indEntEd = fields.Char(
        string="indEntEd")
    esoc02_indEtt = fields.Char(
        string="indEtt", xsd_required=True)
    esoc02_nrRegEtt = fields.Char(
        string="nrRegEtt")
    esoc02_dadosIsencao = fields.Many2one(
        "esoc.02.evtinfoempr.dadosisencao",
        string="Informações Complementares",
        help="Informações Complementares - Empresas Isentas - Dados da"
        "\nIsenção")
    esoc02_contato = fields.Many2one(
        "esoc.02.evtinfoempr.contato",
        string="Informações de contato",
        xsd_required=True)
    esoc02_infoOP = fields.Many2one(
        "esoc.02.evtinfoempr.infoop",
        string="Informações relativas a Órgãos Públicos")
    esoc02_infoOrgInternacional = fields.Many2one(
        "esoc.02.evtinfoempr.infoorginternacional",
        string="infoOrgInternacional",
        help="Informações exclusivas de organismos internacionais e outras"
        "\ninstituições extraterritoriais")
    esoc02_softwareHouse = fields.One2many(
        "esoc.02.evtinfoempr.softwarehouse",
        "esoc02_softwareHouse_TInfoEmpregador_id",
        string="Informações do desenvolvedor do Software"
    )
    esoc02_infoComplementares = fields.Many2one(
        "esoc.02.evtinfoempr.infocomplementares",
        string="Informações complementares sobre o declarante",
        xsd_required=True)


class TPeriodoValidade(spec_models.AbstractSpecMixin):
    "Período de validade das informações"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtinfoempr.tperiodovalidade'
    _generateds_type = 'TPeriodoValidade'
    _concrete_rec_name = 'esoc_iniValid'

    esoc02_iniValid = fields.Char(
        string="iniValid", xsd_required=True)
    esoc02_fimValid = fields.Char(
        string="fimValid")


class Alteracao(spec_models.AbstractSpecMixin):
    "Alteração das informações"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtinfoempr.alteracao'
    _generateds_type = 'alteracaoType'
    _concrete_rec_name = 'esoc_idePeriodo'

    esoc02_idePeriodo = fields.Many2one(
        "esoc.02.evtinfoempr.tideperiodo",
        string="Período de validade das informações alteradas",
        xsd_required=True)
    esoc02_infoCadastro = fields.Many2one(
        "esoc.02.evtinfoempr.tinfoempregador",
        string="Informações do empregador",
        xsd_required=True)
    esoc02_novaValidade = fields.Many2one(
        "esoc.02.evtinfoempr.tperiodovalidade",
        string="Novo período de validade das informações")


class Contato(spec_models.AbstractSpecMixin):
    "Informações de contato"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtinfoempr.contato'
    _generateds_type = 'contatoType'
    _concrete_rec_name = 'esoc_nmCtt'

    esoc02_nmCtt = fields.Char(
        string="nmCtt", xsd_required=True)
    esoc02_cpfCtt = fields.Char(
        string="cpfCtt", xsd_required=True)
    esoc02_foneFixo = fields.Char(
        string="foneFixo")
    esoc02_foneCel = fields.Char(
        string="foneCel")
    esoc02_email = fields.Char(
        string="email")


class DadosIsencao(spec_models.AbstractSpecMixin):
    "Informações Complementares - Empresas Isentas - Dados da Isenção"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtinfoempr.dadosisencao'
    _generateds_type = 'dadosIsencaoType'
    _concrete_rec_name = 'esoc_ideMinLei'

    esoc02_ideMinLei = fields.Char(
        string="ideMinLei", xsd_required=True)
    esoc02_nrCertif = fields.Char(
        string="nrCertif", xsd_required=True)
    esoc02_dtEmisCertif = fields.Date(
        string="dtEmisCertif",
        xsd_required=True)
    esoc02_dtVencCertif = fields.Date(
        string="dtVencCertif",
        xsd_required=True)
    esoc02_nrProtRenov = fields.Char(
        string="nrProtRenov")
    esoc02_dtProtRenov = fields.Date(
        string="dtProtRenov")
    esoc02_dtDou = fields.Date(
        string="dtDou")
    esoc02_pagDou = fields.Integer(
        string="pagDou")


class ESocial(spec_models.AbstractSpecMixin):
    _description = 'esocial'
    _name = 'esoc.02.evtinfoempr.esocial'
    _generateds_type = 'eSocial'
    _concrete_rec_name = 'esoc_evtInfoEmpregador'

    esoc02_evtInfoEmpregador = fields.Many2one(
        "esoc.02.evtinfoempr.evtinfoempregador",
        string="evtInfoEmpregador",
        xsd_required=True)


class EvtInfoEmpregador(spec_models.AbstractSpecMixin):
    "Evento de informações do empregador"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtinfoempr.evtinfoempregador'
    _generateds_type = 'evtInfoEmpregadorType'
    _concrete_rec_name = 'esoc_Id'

    esoc02_Id = fields.Char(
        string="Id", xsd_required=True)
    esoc02_ideEvento = fields.Many2one(
        "esoc.02.evtinfoempr.tidecadastro",
        string="Informações de Identificação do Evento",
        xsd_required=True)
    esoc02_ideEmpregador = fields.Many2one(
        "esoc.02.evtinfoempr.tempregador",
        string="Informações de identificação do empregador",
        xsd_required=True)
    esoc02_infoEmpregador = fields.Many2one(
        "esoc.02.evtinfoempr.infoempregador",
        string="Informações do Empregador",
        xsd_required=True)


class Exclusao(spec_models.AbstractSpecMixin):
    "Exclusão das informações"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtinfoempr.exclusao'
    _generateds_type = 'exclusaoType'
    _concrete_rec_name = 'esoc_idePeriodo'

    esoc02_idePeriodo = fields.Many2one(
        "esoc.02.evtinfoempr.tideperiodo",
        string="Período de validade das informações excluídas",
        xsd_required=True)


class Inclusao(spec_models.AbstractSpecMixin):
    "Inclusão de novas informações"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtinfoempr.inclusao'
    _generateds_type = 'inclusaoType'
    _concrete_rec_name = 'esoc_idePeriodo'

    esoc02_idePeriodo = fields.Many2one(
        "esoc.02.evtinfoempr.tideperiodo",
        string="Período de validade das informações incluídas",
        xsd_required=True)
    esoc02_infoCadastro = fields.Many2one(
        "esoc.02.evtinfoempr.tinfoempregador",
        string="Informações do empregador",
        xsd_required=True)


class InfoComplementares(spec_models.AbstractSpecMixin):
    "Informações complementares sobre o declarante"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtinfoempr.infocomplementares'
    _generateds_type = 'infoComplementaresType'
    _concrete_rec_name = 'esoc_situacaoPJ'

    esoc02_situacaoPJ = fields.Many2one(
        "esoc.02.evtinfoempr.situacaopj",
        string="Informações Complementares",
        help="Informações Complementares - Pessoa Jurídica")
    esoc02_situacaoPF = fields.Many2one(
        "esoc.02.evtinfoempr.situacaopf",
        string="Informações Complementares",
        help="Informações Complementares - Pessoa Física")


class InfoEFR(spec_models.AbstractSpecMixin):
    "Informações relativas a Ente Federativo Responsável - EFR"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtinfoempr.infoefr'
    _generateds_type = 'infoEFRType'
    _concrete_rec_name = 'esoc_ideEFR'

    esoc02_ideEFR = fields.Char(
        string="ideEFR", xsd_required=True)
    esoc02_cnpjEFR = fields.Char(
        string="cnpjEFR")


class InfoEmpregador(spec_models.AbstractSpecMixin):
    "Informações do Empregador"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtinfoempr.infoempregador'
    _generateds_type = 'infoEmpregadorType'
    _concrete_rec_name = 'esoc_inclusao'

    esoc02_choice1 = fields.Selection([
        ('esoc02_inclusao', 'inclusao'),
        ('esoc02_alteracao', 'alteracao'),
        ('esoc02_exclusao', 'exclusao')],
        "inclusao/alteracao/exclusao",
        default="esoc02_inclusao")
    esoc02_inclusao = fields.Many2one(
        "esoc.02.evtinfoempr.inclusao",
        choice='1',
        string="Inclusão de novas informações",
        xsd_required=True)
    esoc02_alteracao = fields.Many2one(
        "esoc.02.evtinfoempr.alteracao",
        choice='1',
        string="Alteração das informações",
        xsd_required=True)
    esoc02_exclusao = fields.Many2one(
        "esoc.02.evtinfoempr.exclusao",
        choice='1',
        string="Exclusão das informações",
        xsd_required=True)


class InfoEnte(spec_models.AbstractSpecMixin):
    """Informações relativas ao ente federativo estadual, distrital ou
    municipal"""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtinfoempr.infoente'
    _generateds_type = 'infoEnteType'
    _concrete_rec_name = 'esoc_nmEnte'

    esoc02_nmEnte = fields.Char(
        string="nmEnte", xsd_required=True)
    esoc02_uf = fields.Selection(
        uf_infoEnte,
        string="uf", xsd_required=True)
    esoc02_codMunic = fields.Integer(
        string="codMunic")
    esoc02_indRPPS = fields.Char(
        string="indRPPS", xsd_required=True)
    esoc02_subteto = fields.Boolean(
        string="subteto", xsd_required=True)
    esoc02_vrSubteto = fields.Monetary(
        string="vrSubteto", xsd_required=True)


class InfoOP(spec_models.AbstractSpecMixin):
    "Informações relativas a Órgãos Públicos"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtinfoempr.infoop'
    _generateds_type = 'infoOPType'
    _concrete_rec_name = 'esoc_nrSiafi'

    esoc02_nrSiafi = fields.Char(
        string="nrSiafi", xsd_required=True)
    esoc02_infoEFR = fields.Many2one(
        "esoc.02.evtinfoempr.infoefr",
        string="Informações relativas a Ente Federativo Responsável",
        help="Informações relativas a Ente Federativo Responsável - EFR")
    esoc02_infoEnte = fields.Many2one(
        "esoc.02.evtinfoempr.infoente",
        string="Informações relativas ao ente federativo estadual",
        help="Informações relativas ao ente federativo estadual, distrital"
        "\nou municipal")


class InfoOrgInternacional(spec_models.AbstractSpecMixin):
    """Informações exclusivas de organismos internacionais e outras
    instituições extraterritoriais"""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtinfoempr.infoorginternacional'
    _generateds_type = 'infoOrgInternacionalType'
    _concrete_rec_name = 'esoc_indAcordoIsenMulta'

    esoc02_indAcordoIsenMulta = fields.Boolean(
        string="indAcordoIsenMulta",
        xsd_required=True)


class SituacaoPF(spec_models.AbstractSpecMixin):
    "Informações Complementares - Pessoa Física"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtinfoempr.situacaopf'
    _generateds_type = 'situacaoPFType'
    _concrete_rec_name = 'esoc_indSitPF'

    esoc02_indSitPF = fields.Boolean(
        string="indSitPF", xsd_required=True)


class SituacaoPJ(spec_models.AbstractSpecMixin):
    "Informações Complementares - Pessoa Jurídica"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtinfoempr.situacaopj'
    _generateds_type = 'situacaoPJType'
    _concrete_rec_name = 'esoc_indSitPJ'

    esoc02_indSitPJ = fields.Boolean(
        string="indSitPJ", xsd_required=True)


class SoftwareHouse(spec_models.AbstractSpecMixin):
    "Informações do desenvolvedor do Software"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtinfoempr.softwarehouse'
    _generateds_type = 'softwareHouseType'
    _concrete_rec_name = 'esoc_cnpjSoftHouse'

    esoc02_softwareHouse_TInfoEmpregador_id = fields.Many2one(
        "esoc.02.evtinfoempr.tinfoempregador")
    esoc02_cnpjSoftHouse = fields.Char(
        string="cnpjSoftHouse",
        xsd_required=True)
    esoc02_nmRazao = fields.Char(
        string="nmRazao", xsd_required=True)
    esoc02_nmCont = fields.Char(
        string="nmCont", xsd_required=True)
    esoc02_telefone = fields.Char(
        string="telefone", xsd_required=True)
    esoc02_email = fields.Char(
        string="email")

# Copyright 2019 Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).
# Generated Fri Mar 29 03:16:33 2019 by generateDS.py(Akretion's branch).
# Python 3.6.7 (default, Oct 22 2018, 11:32:17)  [GCC 8.2.0]
#
import textwrap
from odoo import fields
from .. import spec_models

# Sigla da UF do órgão de classe
ufOC_respReg = [
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
    _name = 'esoc.02.evtexprisco.tempregador'
    _generateds_type = 'TEmpregador'
    _concrete_rec_name = 'esoc_tpInsc'

    esoc02_tpInsc = fields.Boolean(
        string="tpInsc", xsd_required=True)
    esoc02_nrInsc = fields.Char(
        string="nrInsc", xsd_required=True)


class TIdeEveTrab(spec_models.AbstractSpecMixin):
    "Identificação do evento"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtexprisco.tideevetrab'
    _generateds_type = 'TIdeEveTrab'
    _concrete_rec_name = 'esoc_indRetif'

    esoc02_indRetif = fields.Boolean(
        string="indRetif", xsd_required=True)
    esoc02_nrRecibo = fields.Char(
        string="nrRecibo")
    esoc02_tpAmb = fields.Boolean(
        string="tpAmb", xsd_required=True)
    esoc02_procEmi = fields.Boolean(
        string="procEmi", xsd_required=True)
    esoc02_verProc = fields.Char(
        string="verProc", xsd_required=True)


class TIdeVinculoEstag(spec_models.AbstractSpecMixin):
    "Informacoes do Vínculo trabalhista e estagiário"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtexprisco.tidevinculoestag'
    _generateds_type = 'TIdeVinculoEstag'
    _concrete_rec_name = 'esoc_cpfTrab'

    esoc02_cpfTrab = fields.Char(
        string="cpfTrab", xsd_required=True)
    esoc02_nisTrab = fields.Char(
        string="nisTrab")
    esoc02_matricula = fields.Char(
        string="matricula")
    esoc02_codCateg = fields.Integer(
        string="codCateg")


class AtivPericInsal(spec_models.AbstractSpecMixin):
    """Informação da(s) atividade(s) perigosa(s), insalubre(s) ou especial(is)
    desempenhada(s)"""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtexprisco.ativpericinsal'
    _generateds_type = 'ativPericInsalType'
    _concrete_rec_name = 'esoc_codAtiv'

    esoc02_ativPericInsal_infoAtiv_id = fields.Many2one(
        "esoc.02.evtexprisco.infoativ")
    esoc02_codAtiv = fields.Char(
        string="codAtiv", xsd_required=True)


class ESocial(spec_models.AbstractSpecMixin):
    _description = 'esocial'
    _name = 'esoc.02.evtexprisco.esocial'
    _generateds_type = 'eSocial'
    _concrete_rec_name = 'esoc_evtExpRisco'

    esoc02_evtExpRisco = fields.Many2one(
        "esoc.02.evtexprisco.evtexprisco",
        string="evtExpRisco", xsd_required=True)


class EpcEpi(spec_models.AbstractSpecMixin):
    "EPC e EPI"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtexprisco.epcepi'
    _generateds_type = 'epcEpiType'
    _concrete_rec_name = 'esoc_utilizEPC'

    esoc02_utilizEPC = fields.Boolean(
        string="utilizEPC", xsd_required=True)
    esoc02_eficEpc = fields.Char(
        string="eficEpc")
    esoc02_utilizEPI = fields.Boolean(
        string="utilizEPI", xsd_required=True)
    esoc02_epi = fields.One2many(
        "esoc.02.evtexprisco.epi",
        "esoc02_epi_epcEpi_id",
        string="epi"
    )


class Epi(spec_models.AbstractSpecMixin):
    _description = 'epi'
    _name = 'esoc.02.evtexprisco.epi'
    _generateds_type = 'epiType'
    _concrete_rec_name = 'esoc_caEPI'

    esoc02_epi_epcEpi_id = fields.Many2one(
        "esoc.02.evtexprisco.epcepi")
    esoc02_caEPI = fields.Char(
        string="caEPI")
    esoc02_dscEPI = fields.Char(
        string="dscEPI")
    esoc02_eficEpi = fields.Char(
        string="eficEpi", xsd_required=True)
    esoc02_medProtecao = fields.Char(
        string="medProtecao", xsd_required=True)
    esoc02_condFuncto = fields.Char(
        string="condFuncto", xsd_required=True)
    esoc02_usoInint = fields.Char(
        string="usoInint", xsd_required=True)
    esoc02_przValid = fields.Char(
        string="przValid", xsd_required=True)
    esoc02_periodicTroca = fields.Char(
        string="periodicTroca",
        xsd_required=True)
    esoc02_higienizacao = fields.Char(
        string="higienizacao",
        xsd_required=True)


class EvtExpRisco(spec_models.AbstractSpecMixin):
    "Evento Condições Ambientais do Trabalho - Fatores de Risco"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtexprisco.evtexprisco'
    _generateds_type = 'evtExpRiscoType'
    _concrete_rec_name = 'esoc_Id'

    esoc02_Id = fields.Char(
        string="Id", xsd_required=True)
    esoc02_ideEvento = fields.Many2one(
        "esoc.02.evtexprisco.tideevetrab",
        string="Informações de Identificação do Evento",
        xsd_required=True)
    esoc02_ideEmpregador = fields.Many2one(
        "esoc.02.evtexprisco.tempregador",
        string="Informações de identificação do empregador",
        xsd_required=True)
    esoc02_ideVinculo = fields.Many2one(
        "esoc.02.evtexprisco.tidevinculoestag",
        string="Informações de Identificação do Trabalhador e do Vínculo",
        xsd_required=True)
    esoc02_infoExpRisco = fields.Many2one(
        "esoc.02.evtexprisco.infoexprisco",
        string="Ambiente de trabalho",
        xsd_required=True,
        help="Ambiente de trabalho, atividades desempenhadas e exposição a"
        "\nfatores de risco")


class FatRisco(spec_models.AbstractSpecMixin):
    "Fator(es) de risco ao(s) qual(is) o trabalhador está exposto"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtexprisco.fatrisco'
    _generateds_type = 'fatRiscoType'
    _concrete_rec_name = 'esoc_codFatRis'

    esoc02_fatRisco_infoExpRisco_id = fields.Many2one(
        "esoc.02.evtexprisco.infoexprisco")
    esoc02_codFatRis = fields.Char(
        string="codFatRis", xsd_required=True)
    esoc02_tpAval = fields.Boolean(
        string="tpAval", xsd_required=True)
    esoc02_intConc = fields.Monetary(
        string="intConc")
    esoc02_limTol = fields.Monetary(
        string="limTol")
    esoc02_unMed = fields.Boolean(
        string="unMed")
    esoc02_tecMedicao = fields.Char(
        string="tecMedicao")
    esoc02_insalubridade = fields.Char(
        string="insalubridade")
    esoc02_periculosidade = fields.Char(
        string="periculosidade")
    esoc02_aposentEsp = fields.Char(
        string="aposentEsp")
    esoc02_epcEpi = fields.Many2one(
        "esoc.02.evtexprisco.epcepi",
        string="EPC e EPI", xsd_required=True)


class InfoAmb(spec_models.AbstractSpecMixin):
    "Informações relativas ao ambiente de trabalho"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtexprisco.infoamb'
    _generateds_type = 'infoAmbType'
    _concrete_rec_name = 'esoc_codAmb'

    esoc02_infoAmb_infoExpRisco_id = fields.Many2one(
        "esoc.02.evtexprisco.infoexprisco")
    esoc02_codAmb = fields.Char(
        string="codAmb", xsd_required=True)


class InfoAtiv(spec_models.AbstractSpecMixin):
    "Descrição das atividades desempenhadas"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtexprisco.infoativ'
    _generateds_type = 'infoAtivType'
    _concrete_rec_name = 'esoc_dscAtivDes'

    esoc02_dscAtivDes = fields.Char(
        string="dscAtivDes", xsd_required=True)
    esoc02_ativPericInsal = fields.One2many(
        "esoc.02.evtexprisco.ativpericinsal",
        "esoc02_ativPericInsal_infoAtiv_id",
        string="Informação da(s) atividade(s) perigosa(s)",
        xsd_required=True,
        help="Informação da(s) atividade(s) perigosa(s), insalubre(s) ou"
        "\nespecial(is) desempenhada(s)"
    )


class InfoExpRisco(spec_models.AbstractSpecMixin):
    """Ambiente de trabalho, atividades desempenhadas e exposição a fatores de
    risco"""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtexprisco.infoexprisco'
    _generateds_type = 'infoExpRiscoType'
    _concrete_rec_name = 'esoc_dtIniCondicao'

    esoc02_dtIniCondicao = fields.Date(
        string="dtIniCondicao",
        xsd_required=True)
    esoc02_infoAmb = fields.One2many(
        "esoc.02.evtexprisco.infoamb",
        "esoc02_infoAmb_infoExpRisco_id",
        string="Informações relativas ao ambiente de trabalho",
        xsd_required=True
    )
    esoc02_infoAtiv = fields.Many2one(
        "esoc.02.evtexprisco.infoativ",
        string="Descrição das atividades desempenhadas",
        xsd_required=True)
    esoc02_fatRisco = fields.One2many(
        "esoc.02.evtexprisco.fatrisco",
        "esoc02_fatRisco_infoExpRisco_id",
        string="fatRisco", xsd_required=True,
        help="Fator(es) de risco ao(s) qual(is) o trabalhador está exposto"
    )
    esoc02_respReg = fields.One2many(
        "esoc.02.evtexprisco.respreg",
        "esoc02_respReg_infoExpRisco_id",
        string="Responsável pelos registros ambientais",
        xsd_required=True
    )
    esoc02_obs = fields.Many2one(
        "esoc.02.evtexprisco.obs",
        string="Observações relativas a registros ambientais")


class Obs(spec_models.AbstractSpecMixin):
    "Observações relativas a registros ambientais"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtexprisco.obs'
    _generateds_type = 'obsType'
    _concrete_rec_name = 'esoc_metErg'

    esoc02_metErg = fields.Char(
        string="metErg")
    esoc02_obsCompl = fields.Char(
        string="obsCompl")


class RespReg(spec_models.AbstractSpecMixin):
    "Responsável pelos registros ambientais"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtexprisco.respreg'
    _generateds_type = 'respRegType'
    _concrete_rec_name = 'esoc_cpfResp'

    esoc02_respReg_infoExpRisco_id = fields.Many2one(
        "esoc.02.evtexprisco.infoexprisco")
    esoc02_cpfResp = fields.Char(
        string="cpfResp", xsd_required=True)
    esoc02_nisResp = fields.Char(
        string="nisResp", xsd_required=True)
    esoc02_nmResp = fields.Char(
        string="nmResp", xsd_required=True)
    esoc02_ideOC = fields.Boolean(
        string="ideOC", xsd_required=True)
    esoc02_dscOC = fields.Char(
        string="dscOC")
    esoc02_nrOC = fields.Char(
        string="nrOC", xsd_required=True)
    esoc02_ufOC = fields.Selection(
        ufOC_respReg,
        string="ufOC", xsd_required=True)

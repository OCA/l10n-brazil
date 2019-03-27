# Copyright 2019 Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).
# Generated Fri Mar 29 03:16:27 2019 by generateDS.py(Akretion's branch).
# Python 3.6.7 (default, Oct 22 2018, 11:32:17)  [GCC 8.2.0]
#
import textwrap
from odoo import fields
from .. import spec_models

# Sigla da UF
uf_dadosNasc = [
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

# Sigla da UF
uf_TEnderecoBrasil = [
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


class TDadosBenef(spec_models.AbstractSpecMixin):
    "Dados do beneficiário"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtcdbenprr.tdadosbenef'
    _generateds_type = 'TDadosBenef'
    _concrete_rec_name = 'esoc_dadosNasc'

    esoc02_dadosNasc = fields.Many2one(
        "esoc.02.evtcdbenprr.dadosnasc",
        string="Informações de nascimento do beneficiário",
        xsd_required=True)
    esoc02_endereco = fields.Many2one(
        "esoc.02.evtcdbenprr.endereco",
        string="Endereço do Trabalhador",
        xsd_required=True)


class TDadosBeneficio(spec_models.AbstractSpecMixin):
    "Dados do benefício previdenciário"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtcdbenprr.tdadosbeneficio'
    _generateds_type = 'TDadosBeneficio'
    _concrete_rec_name = 'esoc_tpBenef'

    esoc02_tpBenef = fields.Boolean(
        string="tpBenef", xsd_required=True)
    esoc02_nrBenefic = fields.Char(
        string="nrBenefic", xsd_required=True)
    esoc02_dtIniBenef = fields.Date(
        string="dtIniBenef", xsd_required=True)
    esoc02_vrBenef = fields.Monetary(
        string="vrBenef", xsd_required=True)
    esoc02_infoPenMorte = fields.Many2one(
        "esoc.02.evtcdbenprr.infopenmorte",
        string="Informações relativas a pensão por morte")


class TEmprPJ(spec_models.AbstractSpecMixin):
    "Informações do Empregador PJ"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtcdbenprr.temprpj'
    _generateds_type = 'TEmprPJ'
    _concrete_rec_name = 'esoc_tpInsc'

    esoc02_tpInsc = fields.Boolean(
        string="tpInsc", xsd_required=True)
    esoc02_nrInsc = fields.Char(
        string="nrInsc", xsd_required=True)


class TEnderecoBrasil(spec_models.AbstractSpecMixin):
    "Informações do Endereço no Brasil"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtcdbenprr.tenderecobrasil'
    _generateds_type = 'TEnderecoBrasil'
    _concrete_rec_name = 'esoc_tpLograd'

    esoc02_tpLograd = fields.Char(
        string="tpLograd", xsd_required=True)
    esoc02_dscLograd = fields.Char(
        string="dscLograd", xsd_required=True)
    esoc02_nrLograd = fields.Char(
        string="nrLograd", xsd_required=True)
    esoc02_complemento = fields.Char(
        string="complemento")
    esoc02_bairro = fields.Char(
        string="bairro")
    esoc02_cep = fields.Char(
        string="cep", xsd_required=True)
    esoc02_codMunic = fields.Integer(
        string="codMunic", xsd_required=True)
    esoc02_uf = fields.Selection(
        uf_TEnderecoBrasil,
        string="uf", xsd_required=True)


class TEnderecoExterior(spec_models.AbstractSpecMixin):
    "Informações do Endereço no Exterior"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtcdbenprr.tenderecoexterior'
    _generateds_type = 'TEnderecoExterior'
    _concrete_rec_name = 'esoc_paisResid'

    esoc02_paisResid = fields.Char(
        string="paisResid", xsd_required=True)
    esoc02_dscLograd = fields.Char(
        string="dscLograd", xsd_required=True)
    esoc02_nrLograd = fields.Char(
        string="nrLograd", xsd_required=True)
    esoc02_complemento = fields.Char(
        string="complemento")
    esoc02_bairro = fields.Char(
        string="bairro")
    esoc02_nmCid = fields.Char(
        string="nmCid", xsd_required=True)
    esoc02_codPostal = fields.Char(
        string="codPostal")


class TIdeEveTrab(spec_models.AbstractSpecMixin):
    "Identificação do evento"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtcdbenprr.tideevetrab'
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


class DadosNasc(spec_models.AbstractSpecMixin):
    "Informações de nascimento do beneficiário"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtcdbenprr.dadosnasc'
    _generateds_type = 'dadosNascType'
    _concrete_rec_name = 'esoc_dtNascto'

    esoc02_dtNascto = fields.Date(
        string="dtNascto", xsd_required=True)
    esoc02_codMunic = fields.Integer(
        string="codMunic")
    esoc02_uf = fields.Selection(
        uf_dadosNasc,
        string="uf")
    esoc02_paisNascto = fields.Char(
        string="paisNascto", xsd_required=True)
    esoc02_paisNac = fields.Char(
        string="paisNac", xsd_required=True)
    esoc02_nmMae = fields.Char(
        string="nmMae")
    esoc02_nmPai = fields.Char(
        string="nmPai")


class ESocial(spec_models.AbstractSpecMixin):
    _description = 'esocial'
    _name = 'esoc.02.evtcdbenprr.esocial'
    _generateds_type = 'eSocial'
    _concrete_rec_name = 'esoc_evtCdBenPrRP'

    esoc02_evtCdBenPrRP = fields.Many2one(
        "esoc.02.evtcdbenprr.evtcdbenprrp",
        string="evtCdBenPrRP",
        xsd_required=True)


class Endereco(spec_models.AbstractSpecMixin):
    "Endereço do Trabalhador"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtcdbenprr.endereco'
    _generateds_type = 'enderecoType'
    _concrete_rec_name = 'esoc_brasil'

    esoc02_choice1 = fields.Selection([
        ('esoc02_brasil', 'brasil'),
        ('esoc02_exterior', 'exterior')],
        "brasil/exterior",
        default="esoc02_brasil")
    esoc02_brasil = fields.Many2one(
        "esoc.02.evtcdbenprr.tenderecobrasil",
        choice='1',
        string="Endereço no Brasil",
        xsd_required=True)
    esoc02_exterior = fields.Many2one(
        "esoc.02.evtcdbenprr.tenderecoexterior",
        choice='1',
        string="Endereço no Exterior",
        xsd_required=True)


class EvtCdBenPrRP(spec_models.AbstractSpecMixin):
    """Evento de cadastro de benefícios previdenciários de Regimes Próprios"""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtcdbenprr.evtcdbenprrp'
    _generateds_type = 'evtCdBenPrRPType'
    _concrete_rec_name = 'esoc_Id'

    esoc02_Id = fields.Char(
        string="Id", xsd_required=True)
    esoc02_ideEvento = fields.Many2one(
        "esoc.02.evtcdbenprr.tideevetrab",
        string="Informações de Identificação do Evento",
        xsd_required=True)
    esoc02_ideEmpregador = fields.Many2one(
        "esoc.02.evtcdbenprr.temprpj",
        string="Informações de identificação do empregador",
        xsd_required=True)
    esoc02_ideBenef = fields.Many2one(
        "esoc.02.evtcdbenprr.idebenef",
        string="Identificação do beneficiário",
        xsd_required=True)
    esoc02_infoBeneficio = fields.Many2one(
        "esoc.02.evtcdbenprr.infobeneficio",
        string="Informações relacionadas ao benefício previdenciário",
        xsd_required=True)


class FimBeneficio(spec_models.AbstractSpecMixin):
    "Informações relativas a benefícios previdenciários - Término"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtcdbenprr.fimbeneficio'
    _generateds_type = 'fimBeneficioType'
    _concrete_rec_name = 'esoc_tpBenef'

    esoc02_tpBenef = fields.Boolean(
        string="tpBenef", xsd_required=True)
    esoc02_nrBenefic = fields.Char(
        string="nrBenefic", xsd_required=True)
    esoc02_dtFimBenef = fields.Date(
        string="dtFimBenef", xsd_required=True)
    esoc02_mtvFim = fields.Boolean(
        string="mtvFim", xsd_required=True)


class IdeBenef(spec_models.AbstractSpecMixin):
    "Identificação do beneficiário"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtcdbenprr.idebenef'
    _generateds_type = 'ideBenefType'
    _concrete_rec_name = 'esoc_cpfBenef'

    esoc02_cpfBenef = fields.Char(
        string="cpfBenef", xsd_required=True)
    esoc02_nmBenefic = fields.Char(
        string="nmBenefic", xsd_required=True)
    esoc02_dadosBenef = fields.Many2one(
        "esoc.02.evtcdbenprr.tdadosbenef",
        string="Dados do beneficiário",
        xsd_required=True)


class InfoBeneficio(spec_models.AbstractSpecMixin):
    "Informações relacionadas ao benefício previdenciário"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtcdbenprr.infobeneficio'
    _generateds_type = 'infoBeneficioType'
    _concrete_rec_name = 'esoc_tpPlanRP'

    esoc02_tpPlanRP = fields.Boolean(
        string="tpPlanRP", xsd_required=True)
    esoc02_iniBeneficio = fields.Many2one(
        "esoc.02.evtcdbenprr.tdadosbeneficio",
        string="Informações relativas a benefícios previdenciários",
        help="Informações relativas a benefícios previdenciários - Início")
    esoc02_altBeneficio = fields.Many2one(
        "esoc.02.evtcdbenprr.tdadosbeneficio",
        string="Informações relativas a benefícios previdenciários",
        help="Informações relativas a benefícios previdenciários -"
        "\nAlteração")
    esoc02_fimBeneficio = fields.Many2one(
        "esoc.02.evtcdbenprr.fimbeneficio",
        string="Informações relativas a benefícios previdenciários",
        help="Informações relativas a benefícios previdenciários - Término")


class InfoPenMorte(spec_models.AbstractSpecMixin):
    "Informações relativas a pensão por morte"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtcdbenprr.infopenmorte'
    _generateds_type = 'infoPenMorteType'
    _concrete_rec_name = 'esoc_idQuota'

    esoc02_idQuota = fields.Char(
        string="idQuota", xsd_required=True)
    esoc02_cpfInst = fields.Char(
        string="cpfInst", xsd_required=True)

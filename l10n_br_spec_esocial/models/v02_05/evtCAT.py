# Copyright 2019 Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).
# Generated Fri Mar 29 03:16:27 2019 by generateDS.py(Akretion's branch).
# Python 3.6.7 (default, Oct 22 2018, 11:32:17)  [GCC 8.2.0]
#
import textwrap
from odoo import fields
from .. import spec_models

# Sigla da UF do órgão de classe
ufOC_emitente = [
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
uf_localAcidente = [
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
    _name = 'esoc.02.evtcatlib.tempregador'
    _generateds_type = 'TEmpregador'
    _concrete_rec_name = 'esoc_tpInsc'

    esoc02_tpInsc = fields.Boolean(
        string="tpInsc", xsd_required=True)
    esoc02_nrInsc = fields.Char(
        string="nrInsc", xsd_required=True)


class TIdeEveTrab(spec_models.AbstractSpecMixin):
    "Identificação do evento"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtcatlib.tideevetrab'
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


class AgenteCausador(spec_models.AbstractSpecMixin):
    _description = 'agentecausador'
    _name = 'esoc.02.evtcatlib.agentecausador'
    _generateds_type = 'agenteCausadorType'
    _concrete_rec_name = 'esoc_codAgntCausador'

    esoc02_agenteCausador_cat_id = fields.Many2one(
        "esoc.02.evtcatlib.cat")
    esoc02_codAgntCausador = fields.Integer(
        string="codAgntCausador",
        xsd_required=True)


class Atestado(spec_models.AbstractSpecMixin):
    _description = 'atestado'
    _name = 'esoc.02.evtcatlib.atestado'
    _generateds_type = 'atestadoType'
    _concrete_rec_name = 'esoc_codCNES'

    esoc02_codCNES = fields.Char(
        string="codCNES")
    esoc02_dtAtendimento = fields.Date(
        string="dtAtendimento",
        xsd_required=True)
    esoc02_hrAtendimento = fields.Char(
        string="hrAtendimento",
        xsd_required=True)
    esoc02_indInternacao = fields.Char(
        string="indInternacao",
        xsd_required=True)
    esoc02_durTrat = fields.Integer(
        string="durTrat", xsd_required=True)
    esoc02_indAfast = fields.Char(
        string="indAfast", xsd_required=True)
    esoc02_dscLesao = fields.Integer(
        string="dscLesao", xsd_required=True)
    esoc02_dscCompLesao = fields.Char(
        string="dscCompLesao")
    esoc02_diagProvavel = fields.Char(
        string="diagProvavel")
    esoc02_codCID = fields.Char(
        string="codCID", xsd_required=True)
    esoc02_observacao = fields.Char(
        string="observacao")
    esoc02_emitente = fields.Many2one(
        "esoc.02.evtcatlib.emitente",
        string="Médico/Dentista que emitiu o atestado",
        xsd_required=True)


class CatOrigem(spec_models.AbstractSpecMixin):
    "CAT de origem"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtcatlib.catorigem'
    _generateds_type = 'catOrigemType'
    _concrete_rec_name = 'esoc_nrRecCatOrig'

    esoc02_nrRecCatOrig = fields.Char(
        string="nrRecCatOrig",
        xsd_required=True)


class Cat(spec_models.AbstractSpecMixin):
    "Comunicação de Acidente de Trabalho"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtcatlib.cat'
    _generateds_type = 'catType'
    _concrete_rec_name = 'esoc_dtAcid'

    esoc02_dtAcid = fields.Date(
        string="dtAcid", xsd_required=True)
    esoc02_tpAcid = fields.Char(
        string="tpAcid", xsd_required=True)
    esoc02_hrAcid = fields.Char(
        string="hrAcid")
    esoc02_hrsTrabAntesAcid = fields.Char(
        string="hrsTrabAntesAcid",
        xsd_required=True)
    esoc02_tpCat = fields.Boolean(
        string="tpCat", xsd_required=True)
    esoc02_indCatObito = fields.Char(
        string="indCatObito", xsd_required=True)
    esoc02_dtObito = fields.Date(
        string="dtObito")
    esoc02_indComunPolicia = fields.Char(
        string="indComunPolicia",
        xsd_required=True)
    esoc02_codSitGeradora = fields.Integer(
        string="codSitGeradora",
        xsd_required=True)
    esoc02_iniciatCAT = fields.Boolean(
        string="iniciatCAT", xsd_required=True)
    esoc02_obsCAT = fields.Char(
        string="obsCAT")
    esoc02_localAcidente = fields.Many2one(
        "esoc.02.evtcatlib.localacidente",
        string="Local do Acidente",
        xsd_required=True)
    esoc02_parteAtingida = fields.One2many(
        "esoc.02.evtcatlib.parteatingida",
        "esoc02_parteAtingida_cat_id",
        string="Parte do Corpo Atingida",
        xsd_required=True
    )
    esoc02_agenteCausador = fields.One2many(
        "esoc.02.evtcatlib.agentecausador",
        "esoc02_agenteCausador_cat_id",
        string="agenteCausador",
        xsd_required=True
    )
    esoc02_atestado = fields.Many2one(
        "esoc.02.evtcatlib.atestado",
        string="atestado")
    esoc02_catOrigem = fields.Many2one(
        "esoc.02.evtcatlib.catorigem",
        string="CAT de origem")


class ESocial(spec_models.AbstractSpecMixin):
    _description = 'esocial'
    _name = 'esoc.02.evtcatlib.esocial'
    _generateds_type = 'eSocial'
    _concrete_rec_name = 'esoc_evtCAT'

    esoc02_evtCAT = fields.Many2one(
        "esoc.02.evtcatlib.evtcat",
        string="evtCAT", xsd_required=True)


class Emitente(spec_models.AbstractSpecMixin):
    "Médico/Dentista que emitiu o atestado"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtcatlib.emitente'
    _generateds_type = 'emitenteType'
    _concrete_rec_name = 'esoc_nmEmit'

    esoc02_nmEmit = fields.Char(
        string="nmEmit", xsd_required=True)
    esoc02_ideOC = fields.Boolean(
        string="ideOC", xsd_required=True)
    esoc02_nrOC = fields.Char(
        string="nrOC", xsd_required=True)
    esoc02_ufOC = fields.Selection(
        ufOC_emitente,
        string="ufOC")


class EvtCAT(spec_models.AbstractSpecMixin):
    "Evento Comunicação de Acidente de Trabalho"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtcatlib.evtcat'
    _generateds_type = 'evtCATType'
    _concrete_rec_name = 'esoc_Id'

    esoc02_Id = fields.Char(
        string="Id", xsd_required=True)
    esoc02_ideEvento = fields.Many2one(
        "esoc.02.evtcatlib.tideevetrab",
        string="Informações de Identificação do Evento",
        xsd_required=True)
    esoc02_ideEmpregador = fields.Many2one(
        "esoc.02.evtcatlib.tempregador",
        string="Informações de identificação do empregador",
        xsd_required=True)
    esoc02_ideVinculo = fields.Many2one(
        "esoc.02.evtcatlib.idevinculo",
        string="Informações de Identificação do Trabalhador e do Vínculo",
        xsd_required=True)
    esoc02_cat = fields.Many2one(
        "esoc.02.evtcatlib.cat",
        string="Comunicação de Acidente de Trabalho",
        xsd_required=True)


class IdeLocalAcid(spec_models.AbstractSpecMixin):
    "Identificação do local onde ocorreu o acidente"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtcatlib.idelocalacid'
    _generateds_type = 'ideLocalAcidType'
    _concrete_rec_name = 'esoc_tpInsc'

    esoc02_tpInsc = fields.Boolean(
        string="tpInsc", xsd_required=True)
    esoc02_nrInsc = fields.Char(
        string="nrInsc", xsd_required=True)


class IdeVinculo(spec_models.AbstractSpecMixin):
    "Informações de Identificação do Trabalhador e do Vínculo"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtcatlib.idevinculo'
    _generateds_type = 'ideVinculoType'
    _concrete_rec_name = 'esoc_cpfTrab'

    esoc02_cpfTrab = fields.Char(
        string="cpfTrab", xsd_required=True)
    esoc02_nisTrab = fields.Char(
        string="nisTrab")
    esoc02_matricula = fields.Char(
        string="matricula")
    esoc02_codCateg = fields.Integer(
        string="codCateg")


class LocalAcidente(spec_models.AbstractSpecMixin):
    "Local do Acidente"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtcatlib.localacidente'
    _generateds_type = 'localAcidenteType'
    _concrete_rec_name = 'esoc_tpLocal'

    esoc02_tpLocal = fields.Boolean(
        string="tpLocal", xsd_required=True)
    esoc02_dscLocal = fields.Char(
        string="dscLocal")
    esoc02_codAmb = fields.Char(
        string="codAmb")
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
        string="cep")
    esoc02_codMunic = fields.Integer(
        string="codMunic")
    esoc02_uf = fields.Selection(
        uf_localAcidente,
        string="uf")
    esoc02_pais = fields.Char(
        string="pais")
    esoc02_codPostal = fields.Char(
        string="codPostal")
    esoc02_ideLocalAcid = fields.Many2one(
        "esoc.02.evtcatlib.idelocalacid",
        string="Identificação do local onde ocorreu o acidente")


class ParteAtingida(spec_models.AbstractSpecMixin):
    "Parte do Corpo Atingida"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtcatlib.parteatingida'
    _generateds_type = 'parteAtingidaType'
    _concrete_rec_name = 'esoc_codParteAting'

    esoc02_parteAtingida_cat_id = fields.Many2one(
        "esoc.02.evtcatlib.cat")
    esoc02_codParteAting = fields.Integer(
        string="codParteAting",
        xsd_required=True)
    esoc02_lateralidade = fields.Boolean(
        string="lateralidade",
        xsd_required=True)

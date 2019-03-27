# Copyright 2019 Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).
# Generated Fri Mar 29 03:16:39 2019 by generateDS.py(Akretion's branch).
# Python 3.6.7 (default, Oct 22 2018, 11:32:17)  [GCC 8.2.0]
#
import textwrap
from odoo import fields
from .. import spec_models

# UF CRM
ufCRM_medico = [
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

# UF CRM
ufCRM_respMonit = [
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
    _name = 'esoc.02.evtmonitlib.tempregador'
    _generateds_type = 'TEmpregador'
    _concrete_rec_name = 'esoc_tpInsc'

    esoc02_tpInsc = fields.Boolean(
        string="tpInsc", xsd_required=True)
    esoc02_nrInsc = fields.Char(
        string="nrInsc", xsd_required=True)


class TIdeEveTrab(spec_models.AbstractSpecMixin):
    "Identificação do evento"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtmonitlib.tideevetrab'
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
    _name = 'esoc.02.evtmonitlib.tidevinculoestag'
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


class Aso(spec_models.AbstractSpecMixin):
    "Atestado de Saúde Ocupacional (ASO)"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtmonitlib.aso'
    _generateds_type = 'asoType'
    _concrete_rec_name = 'esoc_dtAso'

    esoc02_dtAso = fields.Date(
        string="dtAso", xsd_required=True)
    esoc02_resAso = fields.Boolean(
        string="resAso", xsd_required=True)
    esoc02_exame = fields.One2many(
        "esoc.02.evtmonitlib.exame",
        "esoc02_exame_aso_id",
        string="Avaliações clínicas e exames complementares realizados",
        xsd_required=True
    )
    esoc02_medico = fields.Many2one(
        "esoc.02.evtmonitlib.medico",
        string="Informações sobre o médico emitente do ASO",
        xsd_required=True)


class ESocial(spec_models.AbstractSpecMixin):
    _description = 'esocial'
    _name = 'esoc.02.evtmonitlib.esocial'
    _generateds_type = 'eSocial'
    _concrete_rec_name = 'esoc_evtMonit'

    esoc02_evtMonit = fields.Many2one(
        "esoc.02.evtmonitlib.evtmonit",
        string="evtMonit", xsd_required=True)


class EvtMonit(spec_models.AbstractSpecMixin):
    "Evento Monitoramento da Saúde do Trabalhador"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtmonitlib.evtmonit'
    _generateds_type = 'evtMonitType'
    _concrete_rec_name = 'esoc_Id'

    esoc02_Id = fields.Char(
        string="Id", xsd_required=True)
    esoc02_ideEvento = fields.Many2one(
        "esoc.02.evtmonitlib.tideevetrab",
        string="Informações de Identificação do Evento",
        xsd_required=True)
    esoc02_ideEmpregador = fields.Many2one(
        "esoc.02.evtmonitlib.tempregador",
        string="Informações de identificação do empregador",
        xsd_required=True)
    esoc02_ideVinculo = fields.Many2one(
        "esoc.02.evtmonitlib.tidevinculoestag",
        string="Informações de Identificação do Trabalhador e do Vínculo",
        xsd_required=True)
    esoc02_exMedOcup = fields.Many2one(
        "esoc.02.evtmonitlib.exmedocup",
        string="Informações do exame médico ocupacional",
        xsd_required=True)


class ExMedOcup(spec_models.AbstractSpecMixin):
    "Informações do exame médico ocupacional"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtmonitlib.exmedocup'
    _generateds_type = 'exMedOcupType'
    _concrete_rec_name = 'esoc_tpExameOcup'

    esoc02_tpExameOcup = fields.Boolean(
        string="tpExameOcup", xsd_required=True)
    esoc02_aso = fields.Many2one(
        "esoc.02.evtmonitlib.aso",
        string="Atestado de Saúde Ocupacional (ASO)",
        xsd_required=True)
    esoc02_respMonit = fields.Many2one(
        "esoc.02.evtmonitlib.respmonit",
        string="respMonit", xsd_required=True,
        help="Informações sobre o médico responsável/coordenador do PCMSO")


class Exame(spec_models.AbstractSpecMixin):
    "Avaliações clínicas e exames complementares realizados"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtmonitlib.exame'
    _generateds_type = 'exameType'
    _concrete_rec_name = 'esoc_dtExm'

    esoc02_exame_aso_id = fields.Many2one(
        "esoc.02.evtmonitlib.aso")
    esoc02_dtExm = fields.Date(
        string="dtExm", xsd_required=True)
    esoc02_procRealizado = fields.Integer(
        string="procRealizado",
        xsd_required=True)
    esoc02_obsProc = fields.Char(
        string="obsProc")
    esoc02_ordExame = fields.Boolean(
        string="ordExame", xsd_required=True)
    esoc02_indResult = fields.Boolean(
        string="indResult")


class Medico(spec_models.AbstractSpecMixin):
    "Informações sobre o médico emitente do ASO"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtmonitlib.medico'
    _generateds_type = 'medicoType'
    _concrete_rec_name = 'esoc_cpfMed'

    esoc02_cpfMed = fields.Char(
        string="cpfMed")
    esoc02_nisMed = fields.Char(
        string="nisMed")
    esoc02_nmMed = fields.Char(
        string="nmMed", xsd_required=True)
    esoc02_nrCRM = fields.Char(
        string="nrCRM", xsd_required=True)
    esoc02_ufCRM = fields.Selection(
        ufCRM_medico,
        string="ufCRM", xsd_required=True)


class RespMonit(spec_models.AbstractSpecMixin):
    "Informações sobre o médico responsável/coordenador do PCMSO"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtmonitlib.respmonit'
    _generateds_type = 'respMonitType'
    _concrete_rec_name = 'esoc_cpfResp'

    esoc02_cpfResp = fields.Char(
        string="cpfResp")
    esoc02_nmResp = fields.Char(
        string="nmResp", xsd_required=True)
    esoc02_nrCRM = fields.Char(
        string="nrCRM", xsd_required=True)
    esoc02_ufCRM = fields.Selection(
        ufCRM_respMonit,
        string="ufCRM", xsd_required=True)

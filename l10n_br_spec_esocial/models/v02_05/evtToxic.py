# Copyright 2019 Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).
# Generated Fri Mar 29 03:16:53 2019 by generateDS.py(Akretion's branch).
# Python 3.6.7 (default, Oct 22 2018, 11:32:17)  [GCC 8.2.0]
#
import textwrap
from odoo import fields
from .. import spec_models

# UF CRM
ufCRM_toxicologico = [
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
    _name = 'esoc.02.evttoxiclib.tempregador'
    _generateds_type = 'TEmpregador'
    _concrete_rec_name = 'esoc_tpInsc'

    esoc02_tpInsc = fields.Boolean(
        string="tpInsc", xsd_required=True)
    esoc02_nrInsc = fields.Char(
        string="nrInsc", xsd_required=True)


class TIdeEveTrab(spec_models.AbstractSpecMixin):
    "Identificação do evento"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttoxiclib.tideevetrab'
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
    _name = 'esoc.02.evttoxiclib.tidevinculoestag'
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


class ESocial(spec_models.AbstractSpecMixin):
    _description = 'esocial'
    _name = 'esoc.02.evttoxiclib.esocial'
    _generateds_type = 'eSocial'
    _concrete_rec_name = 'esoc_evtToxic'

    esoc02_evtToxic = fields.Many2one(
        "esoc.02.evttoxiclib.evttoxic",
        string="evtToxic", xsd_required=True)


class EvtToxic(spec_models.AbstractSpecMixin):
    "Evento Exame Toxicológico do Motorista Profissional"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttoxiclib.evttoxic'
    _generateds_type = 'evtToxicType'
    _concrete_rec_name = 'esoc_Id'

    esoc02_Id = fields.Char(
        string="Id", xsd_required=True)
    esoc02_ideEvento = fields.Many2one(
        "esoc.02.evttoxiclib.tideevetrab",
        string="Informações de Identificação do Evento",
        xsd_required=True)
    esoc02_ideEmpregador = fields.Many2one(
        "esoc.02.evttoxiclib.tempregador",
        string="Informações de identificação do empregador",
        xsd_required=True)
    esoc02_ideVinculo = fields.Many2one(
        "esoc.02.evttoxiclib.tidevinculoestag",
        string="Informações de Identificação do Trabalhador e do Vínculo",
        xsd_required=True)
    esoc02_toxicologico = fields.Many2one(
        "esoc.02.evttoxiclib.toxicologico",
        string="toxicologico",
        xsd_required=True,
        help="Informações do exame toxicológico do motorista profissional")


class Toxicologico(spec_models.AbstractSpecMixin):
    "Informações do exame toxicológico do motorista profissional"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttoxiclib.toxicologico'
    _generateds_type = 'toxicologicoType'
    _concrete_rec_name = 'esoc_dtExame'

    esoc02_dtExame = fields.Date(
        string="dtExame", xsd_required=True)
    esoc02_cnpjLab = fields.Char(
        string="cnpjLab")
    esoc02_codSeqExame = fields.Char(
        string="codSeqExame")
    esoc02_nmMed = fields.Char(
        string="nmMed")
    esoc02_nrCRM = fields.Char(
        string="nrCRM")
    esoc02_ufCRM = fields.Selection(
        ufCRM_toxicologico,
        string="ufCRM")
    esoc02_indRecusa = fields.Char(
        string="indRecusa", xsd_required=True)

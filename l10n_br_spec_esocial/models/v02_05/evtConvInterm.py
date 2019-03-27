# Copyright 2019 Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).
# Generated Fri Mar 29 03:16:30 2019 by generateDS.py(Akretion's branch).
# Python 3.6.7 (default, Oct 22 2018, 11:32:17)  [GCC 8.2.0]
#
import textwrap
from odoo import fields
from .. import spec_models

# Sigla da UF
uf_localTrabInterm = [
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
    _name = 'esoc.02.evtconvinte.tempregador'
    _generateds_type = 'TEmpregador'
    _concrete_rec_name = 'esoc_tpInsc'

    esoc02_tpInsc = fields.Boolean(
        string="tpInsc", xsd_required=True)
    esoc02_nrInsc = fields.Char(
        string="nrInsc", xsd_required=True)


class TIdeEveTrab(spec_models.AbstractSpecMixin):
    "Identificação do evento"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtconvinte.tideevetrab'
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


class TIdeVinculoNisObrig(spec_models.AbstractSpecMixin):
    "Informações do Vínculo"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtconvinte.tidevinculonisobrig'
    _generateds_type = 'TIdeVinculoNisObrig'
    _concrete_rec_name = 'esoc_cpfTrab'

    esoc02_cpfTrab = fields.Char(
        string="cpfTrab", xsd_required=True)
    esoc02_nisTrab = fields.Char(
        string="nisTrab", xsd_required=True)
    esoc02_matricula = fields.Char(
        string="matricula", xsd_required=True)


class ESocial(spec_models.AbstractSpecMixin):
    _description = 'esocial'
    _name = 'esoc.02.evtconvinte.esocial'
    _generateds_type = 'eSocial'
    _concrete_rec_name = 'esoc_evtConvInterm'

    esoc02_evtConvInterm = fields.Many2one(
        "esoc.02.evtconvinte.evtconvinterm",
        string="evtConvInterm",
        xsd_required=True)


class EvtConvInterm(spec_models.AbstractSpecMixin):
    "Evento Convocação para Trabalho Intermitente"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtconvinte.evtconvinterm'
    _generateds_type = 'evtConvIntermType'
    _concrete_rec_name = 'esoc_Id'

    esoc02_Id = fields.Char(
        string="Id", xsd_required=True)
    esoc02_ideEvento = fields.Many2one(
        "esoc.02.evtconvinte.tideevetrab",
        string="Informações de Identificação do Evento",
        xsd_required=True)
    esoc02_ideEmpregador = fields.Many2one(
        "esoc.02.evtconvinte.tempregador",
        string="Informações de identificação do empregador",
        xsd_required=True)
    esoc02_ideVinculo = fields.Many2one(
        "esoc.02.evtconvinte.tidevinculonisobrig",
        string="Informações de Identificação do Trabalhador e do Vínculo",
        xsd_required=True)
    esoc02_infoConvInterm = fields.Many2one(
        "esoc.02.evtconvinte.infoconvinterm",
        string="Informações da convocação para trabalho intermitente",
        xsd_required=True)


class InfoConvInterm(spec_models.AbstractSpecMixin):
    "Informações da convocação para trabalho intermitente"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtconvinte.infoconvinterm'
    _generateds_type = 'infoConvIntermType'
    _concrete_rec_name = 'esoc_codConv'

    esoc02_codConv = fields.Char(
        string="codConv", xsd_required=True)
    esoc02_dtInicio = fields.Date(
        string="dtInicio", xsd_required=True)
    esoc02_dtFim = fields.Date(
        string="dtFim", xsd_required=True)
    esoc02_dtPrevPgto = fields.Date(
        string="dtPrevPgto", xsd_required=True)
    esoc02_jornada = fields.Many2one(
        "esoc.02.evtconvinte.jornada",
        string="jornada", xsd_required=True,
        help="Informações da(s) jornada(s) diária(s) da prestação de"
        "\ntrabalho intermitente")
    esoc02_localTrab = fields.Many2one(
        "esoc.02.evtconvinte.localtrab",
        string="Informações do local da prestação de trabalho intermitente",
        xsd_required=True)


class Jornada(spec_models.AbstractSpecMixin):
    """Informações da(s) jornada(s) diária(s) da prestação de trabalho
    intermitente"""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtconvinte.jornada'
    _generateds_type = 'jornadaType'
    _concrete_rec_name = 'esoc_codHorContrat'

    esoc02_codHorContrat = fields.Char(
        string="codHorContrat")
    esoc02_dscJornada = fields.Char(
        string="dscJornada")


class LocalTrabInterm(spec_models.AbstractSpecMixin):
    "Informações do local de trabalho intermitente"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtconvinte.localtrabinterm'
    _generateds_type = 'localTrabIntermType'
    _concrete_rec_name = 'esoc_tpLograd'

    esoc02_tpLograd = fields.Char(
        string="tpLograd", xsd_required=True)
    esoc02_dscLograd = fields.Char(
        string="dscLograd", xsd_required=True)
    esoc02_nrLograd = fields.Char(
        string="nrLograd", xsd_required=True)
    esoc02_complem = fields.Char(
        string="complem")
    esoc02_bairro = fields.Char(
        string="bairro")
    esoc02_cep = fields.Char(
        string="cep", xsd_required=True)
    esoc02_codMunic = fields.Integer(
        string="codMunic", xsd_required=True)
    esoc02_uf = fields.Selection(
        uf_localTrabInterm,
        string="uf", xsd_required=True)


class LocalTrab(spec_models.AbstractSpecMixin):
    "Informações do local da prestação de trabalho intermitente"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtconvinte.localtrab'
    _generateds_type = 'localTrabType'
    _concrete_rec_name = 'esoc_indLocal'

    esoc02_indLocal = fields.Boolean(
        string="indLocal", xsd_required=True)
    esoc02_localTrabInterm = fields.Many2one(
        "esoc.02.evtconvinte.localtrabinterm",
        string="Informações do local de trabalho intermitente")

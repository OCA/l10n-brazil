# Copyright 2019 Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).
# Generated Fri Mar 29 03:16:20 2019 by generateDS.py(Akretion's branch).
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


class TEmpregador(spec_models.AbstractSpecMixin):
    _description = 'tempregador'
    _name = 'esoc.02.evtafasttem.tempregador'
    _generateds_type = 'TEmpregador'
    _concrete_rec_name = 'esoc_tpInsc'

    esoc02_tpInsc = fields.Boolean(
        string="tpInsc", xsd_required=True)
    esoc02_nrInsc = fields.Char(
        string="nrInsc", xsd_required=True)


class TIdeEveTrab(spec_models.AbstractSpecMixin):
    "Identificação do evento"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtafasttem.tideevetrab'
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


class ESocial(spec_models.AbstractSpecMixin):
    _description = 'esocial'
    _name = 'esoc.02.evtafasttem.esocial'
    _generateds_type = 'eSocial'
    _concrete_rec_name = 'esoc_evtAfastTemp'

    esoc02_evtAfastTemp = fields.Many2one(
        "esoc.02.evtafasttem.evtafasttemp",
        string="evtAfastTemp",
        xsd_required=True)


class Emitente(spec_models.AbstractSpecMixin):
    "Médico/Dentista que emitiu o atestado"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtafasttem.emitente'
    _generateds_type = 'emitenteType'
    _concrete_rec_name = 'esoc_nmEmit'

    esoc02_nmEmit = fields.Char(
        string="nmEmit", xsd_required=True)
    esoc02_ideOC = fields.Boolean(
        string="ideOC", xsd_required=True)
    esoc02_nrOc = fields.Char(
        string="nrOc", xsd_required=True)
    esoc02_ufOC = fields.Selection(
        ufOC_emitente,
        string="ufOC")


class EvtAfastTemp(spec_models.AbstractSpecMixin):
    "Evento Afastamento Temporário"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtafasttem.evtafasttemp'
    _generateds_type = 'evtAfastTempType'
    _concrete_rec_name = 'esoc_Id'

    esoc02_Id = fields.Char(
        string="Id", xsd_required=True)
    esoc02_ideEvento = fields.Many2one(
        "esoc.02.evtafasttem.tideevetrab",
        string="Informações de Identificação do Evento",
        xsd_required=True)
    esoc02_ideEmpregador = fields.Many2one(
        "esoc.02.evtafasttem.tempregador",
        string="Informações de identificação do empregador",
        xsd_required=True)
    esoc02_ideVinculo = fields.Many2one(
        "esoc.02.evtafasttem.idevinculo",
        string="Informações de Identificação do Trabalhador e do Vínculo",
        xsd_required=True)
    esoc02_infoAfastamento = fields.Many2one(
        "esoc.02.evtafasttem.infoafastamento",
        string="Informações do Evento",
        xsd_required=True)


class FimAfastamento(spec_models.AbstractSpecMixin):
    "Informações do Término do Afastamento"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtafasttem.fimafastamento'
    _generateds_type = 'fimAfastamentoType'
    _concrete_rec_name = 'esoc_dtTermAfast'

    esoc02_dtTermAfast = fields.Date(
        string="dtTermAfast", xsd_required=True)


class IdeVinculo(spec_models.AbstractSpecMixin):
    "Informações de Identificação do Trabalhador e do Vínculo"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtafasttem.idevinculo'
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


class InfoAfastamento(spec_models.AbstractSpecMixin):
    "Informações do Evento"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtafasttem.infoafastamento'
    _generateds_type = 'infoAfastamentoType'
    _concrete_rec_name = 'esoc_iniAfastamento'

    esoc02_iniAfastamento = fields.Many2one(
        "esoc.02.evtafasttem.iniafastamento",
        string="Informações do Afastamento Temporário",
        help="Informações do Afastamento Temporário - Início")
    esoc02_infoRetif = fields.Many2one(
        "esoc.02.evtafasttem.inforetif",
        string="Informações de retificação do Afastamento Temporário")
    esoc02_fimAfastamento = fields.Many2one(
        "esoc.02.evtafasttem.fimafastamento",
        string="Informações do Término do Afastamento")


class InfoAtestado(spec_models.AbstractSpecMixin):
    "Informações Complementares - Atestado Médico"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtafasttem.infoatestado'
    _generateds_type = 'infoAtestadoType'
    _concrete_rec_name = 'esoc_codCID'

    esoc02_infoAtestado_iniAfastamento_id = fields.Many2one(
        "esoc.02.evtafasttem.iniafastamento")
    esoc02_codCID = fields.Char(
        string="codCID")
    esoc02_qtdDiasAfast = fields.Integer(
        string="qtdDiasAfast",
        xsd_required=True)
    esoc02_emitente = fields.Many2one(
        "esoc.02.evtafasttem.emitente",
        string="Médico/Dentista que emitiu o atestado")


class InfoCessao(spec_models.AbstractSpecMixin):
    "Informações Complementares - Cessão/requisição de trabalhador"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtafasttem.infocessao'
    _generateds_type = 'infoCessaoType'
    _concrete_rec_name = 'esoc_cnpjCess'

    esoc02_cnpjCess = fields.Char(
        string="cnpjCess", xsd_required=True)
    esoc02_infOnus = fields.Boolean(
        string="infOnus", xsd_required=True)


class InfoMandSind(spec_models.AbstractSpecMixin):
    """Informações Complementares - afastamento para exercício de mandato
    sindical"""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtafasttem.infomandsind'
    _generateds_type = 'infoMandSindType'
    _concrete_rec_name = 'esoc_cnpjSind'

    esoc02_cnpjSind = fields.Char(
        string="cnpjSind", xsd_required=True)
    esoc02_infOnusRemun = fields.Boolean(
        string="infOnusRemun",
        xsd_required=True)


class InfoRetif(spec_models.AbstractSpecMixin):
    "Informações de retificação do Afastamento Temporário"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtafasttem.inforetif'
    _generateds_type = 'infoRetifType'
    _concrete_rec_name = 'esoc_origRetif'

    esoc02_origRetif = fields.Boolean(
        string="origRetif", xsd_required=True)
    esoc02_tpProc = fields.Boolean(
        string="tpProc")
    esoc02_nrProc = fields.Char(
        string="nrProc")


class IniAfastamento(spec_models.AbstractSpecMixin):
    "Informações do Afastamento Temporário - Início"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtafasttem.iniafastamento'
    _generateds_type = 'iniAfastamentoType'
    _concrete_rec_name = 'esoc_dtIniAfast'

    esoc02_dtIniAfast = fields.Date(
        string="dtIniAfast", xsd_required=True)
    esoc02_codMotAfast = fields.Char(
        string="codMotAfast", xsd_required=True)
    esoc02_infoMesmoMtv = fields.Char(
        string="infoMesmoMtv")
    esoc02_tpAcidTransito = fields.Boolean(
        string="tpAcidTransito")
    esoc02_observacao = fields.Char(
        string="observacao")
    esoc02_infoAtestado = fields.One2many(
        "esoc.02.evtafasttem.infoatestado",
        "esoc02_infoAtestado_iniAfastamento_id",
        string="Informações Complementares",
        help="Informações Complementares - Atestado Médico"
    )
    esoc02_infoCessao = fields.Many2one(
        "esoc.02.evtafasttem.infocessao",
        string="Informações Complementares",
        help="Informações Complementares - Cessão/requisição de trabalhador")
    esoc02_infoMandSind = fields.Many2one(
        "esoc.02.evtafasttem.infomandsind",
        string="Informações Complementares",
        help="Informações Complementares - afastamento para exercício de"
        "\nmandato sindical")

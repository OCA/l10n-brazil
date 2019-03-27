# Copyright 2019 Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).
# Generated Fri Mar 29 03:16:36 2019 by generateDS.py(Akretion's branch).
# Python 3.6.7 (default, Oct 22 2018, 11:32:17)  [GCC 8.2.0]
#
import textwrap
from odoo import fields
from .. import spec_models


class TEmpregador(spec_models.AbstractSpecMixin):
    _description = 'tempregador'
    _name = 'esoc.02.evtinfocomp.tempregador'
    _generateds_type = 'TEmpregador'
    _concrete_rec_name = 'esoc_tpInsc'

    esoc02_tpInsc = fields.Boolean(
        string="tpInsc", xsd_required=True)
    esoc02_nrInsc = fields.Char(
        string="nrInsc", xsd_required=True)


class TIdeEveFopag(spec_models.AbstractSpecMixin):
    "Identificação do evento periódico"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtinfocomp.tideevefopag'
    _generateds_type = 'TIdeEveFopag'
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
    _name = 'esoc.02.evtinfocomp.esocial'
    _generateds_type = 'eSocial'
    _concrete_rec_name = 'esoc_evtInfoComplPer'

    esoc02_evtInfoComplPer = fields.Many2one(
        "esoc.02.evtinfocomp.evtinfocomplper",
        string="evtInfoComplPer",
        xsd_required=True)


class EvtInfoComplPer(spec_models.AbstractSpecMixin):
    _description = 'evtinfocomplper'
    _name = 'esoc.02.evtinfocomp.evtinfocomplper'
    _generateds_type = 'evtInfoComplPerType'
    _concrete_rec_name = 'esoc_Id'

    esoc02_Id = fields.Char(
        string="Id", xsd_required=True)
    esoc02_ideEvento = fields.Many2one(
        "esoc.02.evtinfocomp.tideevefopag",
        string="Informações de identificação do evento",
        xsd_required=True)
    esoc02_ideEmpregador = fields.Many2one(
        "esoc.02.evtinfocomp.tempregador",
        string="Informações de identificação do empregador",
        xsd_required=True)
    esoc02_infoSubstPatr = fields.Many2one(
        "esoc.02.evtinfocomp.infosubstpatr",
        string="Inf",
        help="Inf. Complementares - Empresas Enquadradas nos artigos 7 a 9"
        "\nda Lei 12.546/2011")
    esoc02_infoSubstPatrOpPort = fields.One2many(
        "esoc.02.evtinfocomp.infosubstpatropport",
        "esoc02_infoSubstPatrOpPort_evtInfoComplPer_id",
        string="Informação de substituição prevista na Lei 12",
        help="Informação de substituição prevista na Lei 12.546/2011"
    )
    esoc02_infoAtivConcom = fields.Many2one(
        "esoc.02.evtinfocomp.infoativconcom",
        string="Empresas enquadradas no Simples Nacional",
        help="Empresas enquadradas no Simples Nacional - Atividades"
        "\nConcomitantes")


class InfoAtivConcom(spec_models.AbstractSpecMixin):
    "Empresas enquadradas no Simples Nacional - Atividades Concomitantes"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtinfocomp.infoativconcom'
    _generateds_type = 'infoAtivConcomType'
    _concrete_rec_name = 'esoc_fatorMes'

    esoc02_fatorMes = fields.Monetary(
        string="fatorMes", xsd_required=True)
    esoc02_fator13 = fields.Monetary(
        string="fator13", xsd_required=True)


class InfoSubstPatrOpPort(spec_models.AbstractSpecMixin):
    "Informação de substituição prevista na Lei 12.546/2011"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtinfocomp.infosubstpatropport'
    _generateds_type = 'infoSubstPatrOpPortType'
    _concrete_rec_name = 'esoc_cnpjOpPortuario'

    esoc02_infoSubstPatrOpPort_evtInfoComplPer_id = fields.Many2one(
        "esoc.02.evtinfocomp.evtinfocomplper")
    esoc02_cnpjOpPortuario = fields.Char(
        string="cnpjOpPortuario",
        xsd_required=True)


class InfoSubstPatr(spec_models.AbstractSpecMixin):
    """Inf. Complementares - Empresas Enquadradas nos artigos 7 a 9 da Lei
    12.546/2011"""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evtinfocomp.infosubstpatr'
    _generateds_type = 'infoSubstPatrType'
    _concrete_rec_name = 'esoc_indSubstPatr'

    esoc02_indSubstPatr = fields.Boolean(
        string="indSubstPatr",
        xsd_required=True)
    esoc02_percRedContrib = fields.Monetary(
        string="percRedContrib",
        xsd_required=True)

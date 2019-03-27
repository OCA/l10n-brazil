# Copyright 2019 Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).
# Generated Fri Mar 29 03:16:45 2019 by generateDS.py(Akretion's branch).
# Python 3.6.7 (default, Oct 22 2018, 11:32:17)  [GCC 8.2.0]
#
import textwrap
from odoo import fields
from .. import spec_models


class TDadosCarreira(spec_models.AbstractSpecMixin):
    "Informações da Carreira"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttabcarre.tdadoscarreira'
    _generateds_type = 'TDadosCarreira'
    _concrete_rec_name = 'esoc_dscCarreira'

    esoc02_dscCarreira = fields.Char(
        string="dscCarreira", xsd_required=True)
    esoc02_leiCarr = fields.Char(
        string="leiCarr")
    esoc02_dtLeiCarr = fields.Date(
        string="dtLeiCarr", xsd_required=True)
    esoc02_sitCarr = fields.Boolean(
        string="sitCarr", xsd_required=True)


class TEmprPJ(spec_models.AbstractSpecMixin):
    "Informações do Empregador PJ"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttabcarre.temprpj'
    _generateds_type = 'TEmprPJ'
    _concrete_rec_name = 'esoc_tpInsc'

    esoc02_tpInsc = fields.Boolean(
        string="tpInsc", xsd_required=True)
    esoc02_nrInsc = fields.Char(
        string="nrInsc", xsd_required=True)


class TIdeCadastro(spec_models.AbstractSpecMixin):
    "Identificação de evento de cadastro/tabelas"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttabcarre.tidecadastro'
    _generateds_type = 'TIdeCadastro'
    _concrete_rec_name = 'esoc_tpAmb'

    esoc02_tpAmb = fields.Boolean(
        string="tpAmb", xsd_required=True)
    esoc02_procEmi = fields.Boolean(
        string="procEmi", xsd_required=True)
    esoc02_verProc = fields.Char(
        string="verProc", xsd_required=True)


class TIdeCarreira(spec_models.AbstractSpecMixin):
    "Identificação da Carreira e período de validade"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttabcarre.tidecarreira'
    _generateds_type = 'TIdeCarreira'
    _concrete_rec_name = 'esoc_codCarreira'

    esoc02_codCarreira = fields.Char(
        string="codCarreira", xsd_required=True)
    esoc02_iniValid = fields.Char(
        string="iniValid", xsd_required=True)
    esoc02_fimValid = fields.Char(
        string="fimValid")


class TPeriodoValidade(spec_models.AbstractSpecMixin):
    "Período de validade das informações"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttabcarre.tperiodovalidade'
    _generateds_type = 'TPeriodoValidade'
    _concrete_rec_name = 'esoc_iniValid'

    esoc02_iniValid = fields.Char(
        string="iniValid", xsd_required=True)
    esoc02_fimValid = fields.Char(
        string="fimValid")


class Alteracao(spec_models.AbstractSpecMixin):
    "Alteração das informações"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttabcarre.alteracao'
    _generateds_type = 'alteracaoType'
    _concrete_rec_name = 'esoc_ideCarreira'

    esoc02_ideCarreira = fields.Many2one(
        "esoc.02.evttabcarre.tidecarreira",
        string="Informações de identificação da Carreira",
        xsd_required=True)
    esoc02_dadosCarreira = fields.Many2one(
        "esoc.02.evttabcarre.tdadoscarreira",
        string="Informações da Carreira",
        xsd_required=True)
    esoc02_novaValidade = fields.Many2one(
        "esoc.02.evttabcarre.tperiodovalidade",
        string="Novo período de validade das informações")


class ESocial(spec_models.AbstractSpecMixin):
    _description = 'esocial'
    _name = 'esoc.02.evttabcarre.esocial'
    _generateds_type = 'eSocial'
    _concrete_rec_name = 'esoc_evtTabCarreira'

    esoc02_evtTabCarreira = fields.Many2one(
        "esoc.02.evttabcarre.evttabcarreira",
        string="evtTabCarreira",
        xsd_required=True)


class EvtTabCarreira(spec_models.AbstractSpecMixin):
    "Evento Tabela de Carreiras Públicas"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttabcarre.evttabcarreira'
    _generateds_type = 'evtTabCarreiraType'
    _concrete_rec_name = 'esoc_Id'

    esoc02_Id = fields.Char(
        string="Id", xsd_required=True)
    esoc02_ideEvento = fields.Many2one(
        "esoc.02.evttabcarre.tidecadastro",
        string="Informações de Identificação do Evento",
        xsd_required=True)
    esoc02_ideEmpregador = fields.Many2one(
        "esoc.02.evttabcarre.temprpj",
        string="Informações de identificação do empregador",
        xsd_required=True)
    esoc02_infoCarreira = fields.Many2one(
        "esoc.02.evttabcarre.infocarreira",
        string="Informações da Carreira",
        xsd_required=True)


class Exclusao(spec_models.AbstractSpecMixin):
    "Exclusão das informações"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttabcarre.exclusao'
    _generateds_type = 'exclusaoType'
    _concrete_rec_name = 'esoc_ideCarreira'

    esoc02_ideCarreira = fields.Many2one(
        "esoc.02.evttabcarre.tidecarreira",
        string="Identificação da Carreira a ser excluída",
        xsd_required=True)


class Inclusao(spec_models.AbstractSpecMixin):
    "Inclusão de novas informações"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttabcarre.inclusao'
    _generateds_type = 'inclusaoType'
    _concrete_rec_name = 'esoc_ideCarreira'

    esoc02_ideCarreira = fields.Many2one(
        "esoc.02.evttabcarre.tidecarreira",
        string="Identificação da Carreira",
        xsd_required=True)
    esoc02_dadosCarreira = fields.Many2one(
        "esoc.02.evttabcarre.tdadoscarreira",
        string="Informações da Carreira",
        xsd_required=True)


class InfoCarreira(spec_models.AbstractSpecMixin):
    "Informações da Carreira"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttabcarre.infocarreira'
    _generateds_type = 'infoCarreiraType'
    _concrete_rec_name = 'esoc_inclusao'

    esoc02_choice1 = fields.Selection([
        ('esoc02_inclusao', 'inclusao'),
        ('esoc02_alteracao', 'alteracao'),
        ('esoc02_exclusao', 'exclusao')],
        "inclusao/alteracao/exclusao",
        default="esoc02_inclusao")
    esoc02_inclusao = fields.Many2one(
        "esoc.02.evttabcarre.inclusao",
        choice='1',
        string="Inclusão de novas informações",
        xsd_required=True)
    esoc02_alteracao = fields.Many2one(
        "esoc.02.evttabcarre.alteracao",
        choice='1',
        string="Alteração das informações",
        xsd_required=True)
    esoc02_exclusao = fields.Many2one(
        "esoc.02.evttabcarre.exclusao",
        choice='1',
        string="Exclusão das informações",
        xsd_required=True)

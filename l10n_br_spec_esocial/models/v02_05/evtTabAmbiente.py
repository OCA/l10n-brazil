# Copyright 2019 Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).
# Generated Fri Mar 29 03:16:43 2019 by generateDS.py(Akretion's branch).
# Python 3.6.7 (default, Oct 22 2018, 11:32:17)  [GCC 8.2.0]
#
import textwrap
from odoo import fields
from .. import spec_models


class TDadosAmbiente(spec_models.AbstractSpecMixin):
    "Informações do ambiente de trabalho"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttabambie.tdadosambiente'
    _generateds_type = 'TDadosAmbiente'
    _concrete_rec_name = 'esoc_nmAmb'

    esoc02_nmAmb = fields.Char(
        string="nmAmb", xsd_required=True)
    esoc02_dscAmb = fields.Char(
        string="dscAmb", xsd_required=True)
    esoc02_localAmb = fields.Boolean(
        string="localAmb", xsd_required=True)
    esoc02_tpInsc = fields.Boolean(
        string="tpInsc")
    esoc02_nrInsc = fields.Char(
        string="nrInsc")
    esoc02_codLotacao = fields.Char(
        string="codLotacao")


class TEmpregador(spec_models.AbstractSpecMixin):
    _description = 'tempregador'
    _name = 'esoc.02.evttabambie.tempregador'
    _generateds_type = 'TEmpregador'
    _concrete_rec_name = 'esoc_tpInsc'

    esoc02_tpInsc = fields.Boolean(
        string="tpInsc", xsd_required=True)
    esoc02_nrInsc = fields.Char(
        string="nrInsc", xsd_required=True)


class TIdeAmbiente(spec_models.AbstractSpecMixin):
    "Informações de identificação do Ambiente de Trabalho"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttabambie.tideambiente'
    _generateds_type = 'TIdeAmbiente'
    _concrete_rec_name = 'esoc_codAmb'

    esoc02_codAmb = fields.Char(
        string="codAmb", xsd_required=True)
    esoc02_iniValid = fields.Char(
        string="iniValid", xsd_required=True)
    esoc02_fimValid = fields.Char(
        string="fimValid")


class TIdeCadastro(spec_models.AbstractSpecMixin):
    "Identificação de evento de cadastro/tabelas"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttabambie.tidecadastro'
    _generateds_type = 'TIdeCadastro'
    _concrete_rec_name = 'esoc_tpAmb'

    esoc02_tpAmb = fields.Boolean(
        string="tpAmb", xsd_required=True)
    esoc02_procEmi = fields.Boolean(
        string="procEmi", xsd_required=True)
    esoc02_verProc = fields.Char(
        string="verProc", xsd_required=True)


class TPeriodoValidade(spec_models.AbstractSpecMixin):
    "Período de validade das informações"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttabambie.tperiodovalidade'
    _generateds_type = 'TPeriodoValidade'
    _concrete_rec_name = 'esoc_iniValid'

    esoc02_iniValid = fields.Char(
        string="iniValid", xsd_required=True)
    esoc02_fimValid = fields.Char(
        string="fimValid")


class Alteracao(spec_models.AbstractSpecMixin):
    "Alteração das informações"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttabambie.alteracao'
    _generateds_type = 'alteracaoType'
    _concrete_rec_name = 'esoc_ideAmbiente'

    esoc02_ideAmbiente = fields.Many2one(
        "esoc.02.evttabambie.tideambiente",
        string="Informações de identificação do Ambiente",
        xsd_required=True)
    esoc02_dadosAmbiente = fields.Many2one(
        "esoc.02.evttabambie.tdadosambiente",
        string="Informações do Ambiente de Trabalho",
        xsd_required=True)
    esoc02_novaValidade = fields.Many2one(
        "esoc.02.evttabambie.tperiodovalidade",
        string="Novo período de validade das informações")


class ESocial(spec_models.AbstractSpecMixin):
    _description = 'esocial'
    _name = 'esoc.02.evttabambie.esocial'
    _generateds_type = 'eSocial'
    _concrete_rec_name = 'esoc_evtTabAmbiente'

    esoc02_evtTabAmbiente = fields.Many2one(
        "esoc.02.evttabambie.evttabambiente",
        string="evtTabAmbiente",
        xsd_required=True)


class EvtTabAmbiente(spec_models.AbstractSpecMixin):
    "Evento Tabela de Ambientes de Trabalho"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttabambie.evttabambiente'
    _generateds_type = 'evtTabAmbienteType'
    _concrete_rec_name = 'esoc_Id'

    esoc02_Id = fields.Char(
        string="Id", xsd_required=True)
    esoc02_ideEvento = fields.Many2one(
        "esoc.02.evttabambie.tidecadastro",
        string="Informações de Identificação do Evento",
        xsd_required=True)
    esoc02_ideEmpregador = fields.Many2one(
        "esoc.02.evttabambie.tempregador",
        string="Informações de identificação do empregador",
        xsd_required=True)
    esoc02_infoAmbiente = fields.Many2one(
        "esoc.02.evttabambie.infoambiente",
        string="Informações do Ambiente",
        xsd_required=True)


class Exclusao(spec_models.AbstractSpecMixin):
    "Exclusão das informações"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttabambie.exclusao'
    _generateds_type = 'exclusaoType'
    _concrete_rec_name = 'esoc_ideAmbiente'

    esoc02_ideAmbiente = fields.Many2one(
        "esoc.02.evttabambie.tideambiente",
        string="Identificação do Ambiente que será excluído",
        xsd_required=True)


class Inclusao(spec_models.AbstractSpecMixin):
    "Inclusão de novas informações"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttabambie.inclusao'
    _generateds_type = 'inclusaoType'
    _concrete_rec_name = 'esoc_ideAmbiente'

    esoc02_ideAmbiente = fields.Many2one(
        "esoc.02.evttabambie.tideambiente",
        string="ideAmbiente", xsd_required=True,
        help="Informações de identificação do ambiente de trabalho do"
        "\nempregador")
    esoc02_dadosAmbiente = fields.Many2one(
        "esoc.02.evttabambie.tdadosambiente",
        string="Informações do ambiente de trabalho",
        xsd_required=True)


class InfoAmbiente(spec_models.AbstractSpecMixin):
    "Informações do Ambiente"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttabambie.infoambiente'
    _generateds_type = 'infoAmbienteType'
    _concrete_rec_name = 'esoc_inclusao'

    esoc02_choice1 = fields.Selection([
        ('esoc02_inclusao', 'inclusao'),
        ('esoc02_alteracao', 'alteracao'),
        ('esoc02_exclusao', 'exclusao')],
        "inclusao/alteracao/exclusao",
        default="esoc02_inclusao")
    esoc02_inclusao = fields.Many2one(
        "esoc.02.evttabambie.inclusao",
        choice='1',
        string="Inclusão de novas informações",
        xsd_required=True)
    esoc02_alteracao = fields.Many2one(
        "esoc.02.evttabambie.alteracao",
        choice='1',
        string="Alteração das informações",
        xsd_required=True)
    esoc02_exclusao = fields.Many2one(
        "esoc.02.evttabambie.exclusao",
        choice='1',
        string="Exclusão das informações",
        xsd_required=True)

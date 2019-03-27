# Copyright 2019 Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).
# Generated Fri Mar 29 03:16:48 2019 by generateDS.py(Akretion's branch).
# Python 3.6.7 (default, Oct 22 2018, 11:32:17)  [GCC 8.2.0]
#
import textwrap
from odoo import fields
from .. import spec_models


class TDadosOperPortuario(spec_models.AbstractSpecMixin):
    "Informações do Operador Portuário"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttaboperp.tdadosoperportuario'
    _generateds_type = 'TDadosOperPortuario'
    _concrete_rec_name = 'esoc_aliqRat'

    esoc02_aliqRat = fields.Integer(
        string="aliqRat", xsd_required=True)
    esoc02_fap = fields.Monetary(
        string="fap", xsd_required=True)
    esoc02_aliqRatAjust = fields.Monetary(
        string="aliqRatAjust",
        xsd_required=True)


class TEmpregador(spec_models.AbstractSpecMixin):
    _description = 'tempregador'
    _name = 'esoc.02.evttaboperp.tempregador'
    _generateds_type = 'TEmpregador'
    _concrete_rec_name = 'esoc_tpInsc'

    esoc02_tpInsc = fields.Boolean(
        string="tpInsc", xsd_required=True)
    esoc02_nrInsc = fields.Char(
        string="nrInsc", xsd_required=True)


class TIdeCadastro(spec_models.AbstractSpecMixin):
    "Identificação de evento de cadastro/tabelas"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttaboperp.tidecadastro'
    _generateds_type = 'TIdeCadastro'
    _concrete_rec_name = 'esoc_tpAmb'

    esoc02_tpAmb = fields.Boolean(
        string="tpAmb", xsd_required=True)
    esoc02_procEmi = fields.Boolean(
        string="procEmi", xsd_required=True)
    esoc02_verProc = fields.Char(
        string="verProc", xsd_required=True)


class TIdeOperPortuario(spec_models.AbstractSpecMixin):
    "Informações de identificação do Operador Portuário"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttaboperp.tideoperportuario'
    _generateds_type = 'TIdeOperPortuario'
    _concrete_rec_name = 'esoc_cnpjOpPortuario'

    esoc02_cnpjOpPortuario = fields.Char(
        string="cnpjOpPortuario",
        xsd_required=True)
    esoc02_iniValid = fields.Char(
        string="iniValid", xsd_required=True)
    esoc02_fimValid = fields.Char(
        string="fimValid")


class TPeriodoValidade(spec_models.AbstractSpecMixin):
    "Período de validade das informações"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttaboperp.tperiodovalidade'
    _generateds_type = 'TPeriodoValidade'
    _concrete_rec_name = 'esoc_iniValid'

    esoc02_iniValid = fields.Char(
        string="iniValid", xsd_required=True)
    esoc02_fimValid = fields.Char(
        string="fimValid")


class Alteracao(spec_models.AbstractSpecMixin):
    "Alteração das informações"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttaboperp.alteracao'
    _generateds_type = 'alteracaoType'
    _concrete_rec_name = 'esoc_ideOperPortuario'

    esoc02_ideOperPortuario = fields.Many2one(
        "esoc.02.evttaboperp.tideoperportuario",
        string="Informações de identificação do Operador Portuário",
        xsd_required=True)
    esoc02_dadosOperPortuario = fields.Many2one(
        "esoc.02.evttaboperp.tdadosoperportuario",
        string="Informações do Operador Portuário",
        xsd_required=True)
    esoc02_novaValidade = fields.Many2one(
        "esoc.02.evttaboperp.tperiodovalidade",
        string="Novo período de validade das informações")


class ESocial(spec_models.AbstractSpecMixin):
    _description = 'esocial'
    _name = 'esoc.02.evttaboperp.esocial'
    _generateds_type = 'eSocial'
    _concrete_rec_name = 'esoc_evtTabOperPort'

    esoc02_evtTabOperPort = fields.Many2one(
        "esoc.02.evttaboperp.evttaboperport",
        string="evtTabOperPort",
        xsd_required=True)


class EvtTabOperPort(spec_models.AbstractSpecMixin):
    "Evento Tabela de Operadores Portuários"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttaboperp.evttaboperport'
    _generateds_type = 'evtTabOperPortType'
    _concrete_rec_name = 'esoc_Id'

    esoc02_Id = fields.Char(
        string="Id", xsd_required=True)
    esoc02_ideEvento = fields.Many2one(
        "esoc.02.evttaboperp.tidecadastro",
        string="Informações de Identificação do Evento",
        xsd_required=True)
    esoc02_ideEmpregador = fields.Many2one(
        "esoc.02.evttaboperp.tempregador",
        string="Informações de identificação do empregador",
        xsd_required=True)
    esoc02_infoOperPortuario = fields.Many2one(
        "esoc.02.evttaboperp.infooperportuario",
        string="Informações do Operador Portuário",
        xsd_required=True)


class Exclusao(spec_models.AbstractSpecMixin):
    "Exclusão das informações"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttaboperp.exclusao'
    _generateds_type = 'exclusaoType'
    _concrete_rec_name = 'esoc_ideOperPortuario'

    esoc02_ideOperPortuario = fields.Many2one(
        "esoc.02.evttaboperp.tideoperportuario",
        string="Identificação do Operador Portuário que será excluído",
        xsd_required=True)


class Inclusao(spec_models.AbstractSpecMixin):
    "Inclusão de novas informações"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttaboperp.inclusao'
    _generateds_type = 'inclusaoType'
    _concrete_rec_name = 'esoc_ideOperPortuario'

    esoc02_ideOperPortuario = fields.Many2one(
        "esoc.02.evttaboperp.tideoperportuario",
        string="Identificação do Operador Portuário",
        xsd_required=True)
    esoc02_dadosOperPortuario = fields.Many2one(
        "esoc.02.evttaboperp.tdadosoperportuario",
        string="Informações do Operador Portuário",
        xsd_required=True)


class InfoOperPortuario(spec_models.AbstractSpecMixin):
    "Informações do Operador Portuário"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttaboperp.infooperportuario'
    _generateds_type = 'infoOperPortuarioType'
    _concrete_rec_name = 'esoc_inclusao'

    esoc02_choice1 = fields.Selection([
        ('esoc02_inclusao', 'inclusao'),
        ('esoc02_alteracao', 'alteracao'),
        ('esoc02_exclusao', 'exclusao')],
        "inclusao/alteracao/exclusao",
        default="esoc02_inclusao")
    esoc02_inclusao = fields.Many2one(
        "esoc.02.evttaboperp.inclusao",
        choice='1',
        string="Inclusão de novas informações",
        xsd_required=True)
    esoc02_alteracao = fields.Many2one(
        "esoc.02.evttaboperp.alteracao",
        choice='1',
        string="Alteração das informações",
        xsd_required=True)
    esoc02_exclusao = fields.Many2one(
        "esoc.02.evttaboperp.exclusao",
        choice='1',
        string="Exclusão das informações",
        xsd_required=True)

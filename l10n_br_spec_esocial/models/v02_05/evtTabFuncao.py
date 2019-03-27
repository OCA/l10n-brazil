# Copyright 2019 Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).
# Generated Fri Mar 29 03:16:46 2019 by generateDS.py(Akretion's branch).
# Python 3.6.7 (default, Oct 22 2018, 11:32:17)  [GCC 8.2.0]
#
import textwrap
from odoo import fields
from .. import spec_models


class TDadosFuncao(spec_models.AbstractSpecMixin):
    "Informações da Função"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttabfunca.tdadosfuncao'
    _generateds_type = 'TDadosFuncao'
    _concrete_rec_name = 'esoc_dscFuncao'

    esoc02_dscFuncao = fields.Char(
        string="dscFuncao", xsd_required=True)
    esoc02_codCBO = fields.Char(
        string="codCBO", xsd_required=True)


class TEmpregador(spec_models.AbstractSpecMixin):
    _description = 'tempregador'
    _name = 'esoc.02.evttabfunca.tempregador'
    _generateds_type = 'TEmpregador'
    _concrete_rec_name = 'esoc_tpInsc'

    esoc02_tpInsc = fields.Boolean(
        string="tpInsc", xsd_required=True)
    esoc02_nrInsc = fields.Char(
        string="nrInsc", xsd_required=True)


class TIdeCadastro(spec_models.AbstractSpecMixin):
    "Identificação de evento de cadastro/tabelas"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttabfunca.tidecadastro'
    _generateds_type = 'TIdeCadastro'
    _concrete_rec_name = 'esoc_tpAmb'

    esoc02_tpAmb = fields.Boolean(
        string="tpAmb", xsd_required=True)
    esoc02_procEmi = fields.Boolean(
        string="procEmi", xsd_required=True)
    esoc02_verProc = fields.Char(
        string="verProc", xsd_required=True)


class TIdeFuncao(spec_models.AbstractSpecMixin):
    "Identificação da Função e período de validade"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttabfunca.tidefuncao'
    _generateds_type = 'TIdeFuncao'
    _concrete_rec_name = 'esoc_codFuncao'

    esoc02_codFuncao = fields.Char(
        string="codFuncao", xsd_required=True)
    esoc02_iniValid = fields.Char(
        string="iniValid", xsd_required=True)
    esoc02_fimValid = fields.Char(
        string="fimValid")


class TPeriodoValidade(spec_models.AbstractSpecMixin):
    "Período de validade das informações"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttabfunca.tperiodovalidade'
    _generateds_type = 'TPeriodoValidade'
    _concrete_rec_name = 'esoc_iniValid'

    esoc02_iniValid = fields.Char(
        string="iniValid", xsd_required=True)
    esoc02_fimValid = fields.Char(
        string="fimValid")


class Alteracao(spec_models.AbstractSpecMixin):
    "Alteração das informações"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttabfunca.alteracao'
    _generateds_type = 'alteracaoType'
    _concrete_rec_name = 'esoc_ideFuncao'

    esoc02_ideFuncao = fields.Many2one(
        "esoc.02.evttabfunca.tidefuncao",
        string="Informações de identificação da função",
        xsd_required=True)
    esoc02_dadosFuncao = fields.Many2one(
        "esoc.02.evttabfunca.tdadosfuncao",
        string="Informações da função",
        xsd_required=True)
    esoc02_novaValidade = fields.Many2one(
        "esoc.02.evttabfunca.tperiodovalidade",
        string="Novo período de validade das informações")


class ESocial(spec_models.AbstractSpecMixin):
    _description = 'esocial'
    _name = 'esoc.02.evttabfunca.esocial'
    _generateds_type = 'eSocial'
    _concrete_rec_name = 'esoc_evtTabFuncao'

    esoc02_evtTabFuncao = fields.Many2one(
        "esoc.02.evttabfunca.evttabfuncao",
        string="evtTabFuncao",
        xsd_required=True)


class EvtTabFuncao(spec_models.AbstractSpecMixin):
    "Evento Tabela de Funções"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttabfunca.evttabfuncao'
    _generateds_type = 'evtTabFuncaoType'
    _concrete_rec_name = 'esoc_Id'

    esoc02_Id = fields.Char(
        string="Id", xsd_required=True)
    esoc02_ideEvento = fields.Many2one(
        "esoc.02.evttabfunca.tidecadastro",
        string="Informações de Identificação do Evento",
        xsd_required=True)
    esoc02_ideEmpregador = fields.Many2one(
        "esoc.02.evttabfunca.tempregador",
        string="Informações de identificação do empregador",
        xsd_required=True)
    esoc02_infoFuncao = fields.Many2one(
        "esoc.02.evttabfunca.infofuncao",
        string="Informações da Função",
        xsd_required=True)


class Exclusao(spec_models.AbstractSpecMixin):
    "Exclusão das informações"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttabfunca.exclusao'
    _generateds_type = 'exclusaoType'
    _concrete_rec_name = 'esoc_ideFuncao'

    esoc02_ideFuncao = fields.Many2one(
        "esoc.02.evttabfunca.tidefuncao",
        string="Identificação da função que será excluído",
        xsd_required=True)


class Inclusao(spec_models.AbstractSpecMixin):
    "Inclusão de novas informações"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttabfunca.inclusao'
    _generateds_type = 'inclusaoType'
    _concrete_rec_name = 'esoc_ideFuncao'

    esoc02_ideFuncao = fields.Many2one(
        "esoc.02.evttabfunca.tidefuncao",
        string="Identificação da Função",
        xsd_required=True)
    esoc02_dadosFuncao = fields.Many2one(
        "esoc.02.evttabfunca.tdadosfuncao",
        string="Informações da Função",
        xsd_required=True)


class InfoFuncao(spec_models.AbstractSpecMixin):
    "Informações da Função"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttabfunca.infofuncao'
    _generateds_type = 'infoFuncaoType'
    _concrete_rec_name = 'esoc_inclusao'

    esoc02_choice1 = fields.Selection([
        ('esoc02_inclusao', 'inclusao'),
        ('esoc02_alteracao', 'alteracao'),
        ('esoc02_exclusao', 'exclusao')],
        "inclusao/alteracao/exclusao",
        default="esoc02_inclusao")
    esoc02_inclusao = fields.Many2one(
        "esoc.02.evttabfunca.inclusao",
        choice='1',
        string="Inclusão de novas informações",
        xsd_required=True)
    esoc02_alteracao = fields.Many2one(
        "esoc.02.evttabfunca.alteracao",
        choice='1',
        string="Alteração das informações",
        xsd_required=True)
    esoc02_exclusao = fields.Many2one(
        "esoc.02.evttabfunca.exclusao",
        choice='1',
        string="Exclusão das informações",
        xsd_required=True)

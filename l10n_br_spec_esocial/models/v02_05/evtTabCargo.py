# Copyright 2019 Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).
# Generated Fri Mar 29 03:16:44 2019 by generateDS.py(Akretion's branch).
# Python 3.6.7 (default, Oct 22 2018, 11:32:17)  [GCC 8.2.0]
#
import textwrap
from odoo import fields
from .. import spec_models


class TDadosCargo(spec_models.AbstractSpecMixin):
    "Informações do Cargo"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttabcargo.tdadoscargo'
    _generateds_type = 'TDadosCargo'
    _concrete_rec_name = 'esoc_nmCargo'

    esoc02_nmCargo = fields.Char(
        string="nmCargo", xsd_required=True)
    esoc02_codCBO = fields.Char(
        string="codCBO", xsd_required=True)
    esoc02_cargoPublico = fields.Many2one(
        "esoc.02.evttabcargo.cargopublico",
        string="cargoPublico",
        help="Detalhamento de informações exclusivas para Cargos e Empregos"
        "\nPúblicos")


class TEmpregador(spec_models.AbstractSpecMixin):
    _description = 'tempregador'
    _name = 'esoc.02.evttabcargo.tempregador'
    _generateds_type = 'TEmpregador'
    _concrete_rec_name = 'esoc_tpInsc'

    esoc02_tpInsc = fields.Boolean(
        string="tpInsc", xsd_required=True)
    esoc02_nrInsc = fields.Char(
        string="nrInsc", xsd_required=True)


class TIdeCadastro(spec_models.AbstractSpecMixin):
    "Identificação de evento de cadastro/tabelas"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttabcargo.tidecadastro'
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
    _name = 'esoc.02.evttabcargo.tperiodovalidade'
    _generateds_type = 'TPeriodoValidade'
    _concrete_rec_name = 'esoc_iniValid'

    esoc02_iniValid = fields.Char(
        string="iniValid", xsd_required=True)
    esoc02_fimValid = fields.Char(
        string="fimValid")


class TideCargo(spec_models.AbstractSpecMixin):
    "Identificação do cargo e período de validade"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttabcargo.tidecargo'
    _generateds_type = 'TideCargo'
    _concrete_rec_name = 'esoc_codCargo'

    esoc02_codCargo = fields.Char(
        string="codCargo", xsd_required=True)
    esoc02_iniValid = fields.Char(
        string="iniValid", xsd_required=True)
    esoc02_fimValid = fields.Char(
        string="fimValid")


class Alteracao(spec_models.AbstractSpecMixin):
    "Alteração das informações"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttabcargo.alteracao'
    _generateds_type = 'alteracaoType'
    _concrete_rec_name = 'esoc_ideCargo'

    esoc02_ideCargo = fields.Many2one(
        "esoc.02.evttabcargo.tidecargo",
        string="Informações de identificação do cargo",
        xsd_required=True)
    esoc02_dadosCargo = fields.Many2one(
        "esoc.02.evttabcargo.tdadoscargo",
        string="Informações do cargo",
        xsd_required=True)
    esoc02_novaValidade = fields.Many2one(
        "esoc.02.evttabcargo.tperiodovalidade",
        string="Novo período de validade das informações")


class CargoPublico(spec_models.AbstractSpecMixin):
    """Detalhamento de informações exclusivas para Cargos e Empregos
    Públicos"""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttabcargo.cargopublico'
    _generateds_type = 'cargoPublicoType'
    _concrete_rec_name = 'esoc_acumCargo'

    esoc02_acumCargo = fields.Boolean(
        string="acumCargo", xsd_required=True)
    esoc02_contagemEsp = fields.Boolean(
        string="contagemEsp", xsd_required=True)
    esoc02_dedicExcl = fields.Char(
        string="dedicExcl", xsd_required=True)
    esoc02_leiCargo = fields.Many2one(
        "esoc.02.evttabcargo.leicargo",
        string="Lei que criou/extinguiu/reestruturou o cargo",
        xsd_required=True)


class ESocial(spec_models.AbstractSpecMixin):
    _description = 'esocial'
    _name = 'esoc.02.evttabcargo.esocial'
    _generateds_type = 'eSocial'
    _concrete_rec_name = 'esoc_evtTabCargo'

    esoc02_evtTabCargo = fields.Many2one(
        "esoc.02.evttabcargo.evttabcargo",
        string="evtTabCargo", xsd_required=True)


class EvtTabCargo(spec_models.AbstractSpecMixin):
    "Evento Tabela de Cargos"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttabcargo.evttabcargo'
    _generateds_type = 'evtTabCargoType'
    _concrete_rec_name = 'esoc_Id'

    esoc02_Id = fields.Char(
        string="Id", xsd_required=True)
    esoc02_ideEvento = fields.Many2one(
        "esoc.02.evttabcargo.tidecadastro",
        string="Informações de Identificação do Evento",
        xsd_required=True)
    esoc02_ideEmpregador = fields.Many2one(
        "esoc.02.evttabcargo.tempregador",
        string="Informações de identificação do empregador",
        xsd_required=True)
    esoc02_infoCargo = fields.Many2one(
        "esoc.02.evttabcargo.infocargo",
        string="Informações do cargo",
        xsd_required=True)


class Exclusao(spec_models.AbstractSpecMixin):
    "Exclusão das informações"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttabcargo.exclusao'
    _generateds_type = 'exclusaoType'
    _concrete_rec_name = 'esoc_ideCargo'

    esoc02_ideCargo = fields.Many2one(
        "esoc.02.evttabcargo.tidecargo",
        string="Identificação do registro que será excluído",
        xsd_required=True)


class Inclusao(spec_models.AbstractSpecMixin):
    "Inclusão de novas informações"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttabcargo.inclusao'
    _generateds_type = 'inclusaoType'
    _concrete_rec_name = 'esoc_ideCargo'

    esoc02_ideCargo = fields.Many2one(
        "esoc.02.evttabcargo.tidecargo",
        string="Identificação do Cargo",
        xsd_required=True)
    esoc02_dadosCargo = fields.Many2one(
        "esoc.02.evttabcargo.tdadoscargo",
        string="Informações do Cargo",
        xsd_required=True)


class InfoCargo(spec_models.AbstractSpecMixin):
    "Informações do cargo"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttabcargo.infocargo'
    _generateds_type = 'infoCargoType'
    _concrete_rec_name = 'esoc_inclusao'

    esoc02_choice1 = fields.Selection([
        ('esoc02_inclusao', 'inclusao'),
        ('esoc02_alteracao', 'alteracao'),
        ('esoc02_exclusao', 'exclusao')],
        "inclusao/alteracao/exclusao",
        default="esoc02_inclusao")
    esoc02_inclusao = fields.Many2one(
        "esoc.02.evttabcargo.inclusao",
        choice='1',
        string="Inclusão de novas informações",
        xsd_required=True)
    esoc02_alteracao = fields.Many2one(
        "esoc.02.evttabcargo.alteracao",
        choice='1',
        string="Alteração das informações",
        xsd_required=True)
    esoc02_exclusao = fields.Many2one(
        "esoc.02.evttabcargo.exclusao",
        choice='1',
        string="Exclusão das informações",
        xsd_required=True)


class LeiCargo(spec_models.AbstractSpecMixin):
    "Lei que criou/extinguiu/reestruturou o cargo"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttabcargo.leicargo'
    _generateds_type = 'leiCargoType'
    _concrete_rec_name = 'esoc_nrLei'

    esoc02_nrLei = fields.Char(
        string="nrLei", xsd_required=True)
    esoc02_dtLei = fields.Date(
        string="dtLei", xsd_required=True)
    esoc02_sitCargo = fields.Boolean(
        string="sitCargo", xsd_required=True)

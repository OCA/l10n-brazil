# Copyright 2019 Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).
# Generated Fri Mar 29 03:16:48 2019 by generateDS.py(Akretion's branch).
# Python 3.6.7 (default, Oct 22 2018, 11:32:17)  [GCC 8.2.0]
#
import textwrap
from odoo import fields
from .. import spec_models


class TDadosLotacao(spec_models.AbstractSpecMixin):
    "Informações da Lotação"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttablotac.tdadoslotacao'
    _generateds_type = 'TDadosLotacao'
    _concrete_rec_name = 'esoc_tpLotacao'

    esoc02_tpLotacao = fields.Char(
        string="tpLotacao", xsd_required=True)
    esoc02_tpInsc = fields.Boolean(
        string="tpInsc")
    esoc02_nrInsc = fields.Char(
        string="nrInsc")
    esoc02_fpasLotacao = fields.Many2one(
        "esoc.02.evttablotac.fpaslotacao",
        string="fpasLotacao", xsd_required=True,
        help="Informações de FPAS e Terceiros relativas à lotação"
        "\ntributária")
    esoc02_infoEmprParcial = fields.Many2one(
        "esoc.02.evttablotac.infoemprparcial",
        string="Informação complementar de obra de construção civil")


class TEmpregador(spec_models.AbstractSpecMixin):
    _description = 'tempregador'
    _name = 'esoc.02.evttablotac.tempregador'
    _generateds_type = 'TEmpregador'
    _concrete_rec_name = 'esoc_tpInsc'

    esoc02_tpInsc = fields.Boolean(
        string="tpInsc", xsd_required=True)
    esoc02_nrInsc = fields.Char(
        string="nrInsc", xsd_required=True)


class TIdeCadastro(spec_models.AbstractSpecMixin):
    "Identificação de evento de cadastro/tabelas"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttablotac.tidecadastro'
    _generateds_type = 'TIdeCadastro'
    _concrete_rec_name = 'esoc_tpAmb'

    esoc02_tpAmb = fields.Boolean(
        string="tpAmb", xsd_required=True)
    esoc02_procEmi = fields.Boolean(
        string="procEmi", xsd_required=True)
    esoc02_verProc = fields.Char(
        string="verProc", xsd_required=True)


class TIdeLotacao(spec_models.AbstractSpecMixin):
    "Identificação da Lotação e período de validade"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttablotac.tidelotacao'
    _generateds_type = 'TIdeLotacao'
    _concrete_rec_name = 'esoc_codLotacao'

    esoc02_codLotacao = fields.Char(
        string="codLotacao", xsd_required=True)
    esoc02_iniValid = fields.Char(
        string="iniValid", xsd_required=True)
    esoc02_fimValid = fields.Char(
        string="fimValid")


class TPeriodoValidade(spec_models.AbstractSpecMixin):
    "Período de validade das informações"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttablotac.tperiodovalidade'
    _generateds_type = 'TPeriodoValidade'
    _concrete_rec_name = 'esoc_iniValid'

    esoc02_iniValid = fields.Char(
        string="iniValid", xsd_required=True)
    esoc02_fimValid = fields.Char(
        string="fimValid")


class Alteracao(spec_models.AbstractSpecMixin):
    "Alteração das informações"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttablotac.alteracao'
    _generateds_type = 'alteracaoType'
    _concrete_rec_name = 'esoc_ideLotacao'

    esoc02_ideLotacao = fields.Many2one(
        "esoc.02.evttablotac.tidelotacao",
        string="Informações de identificação da lotação",
        xsd_required=True)
    esoc02_dadosLotacao = fields.Many2one(
        "esoc.02.evttablotac.tdadoslotacao",
        string="Informações da lotação",
        xsd_required=True)
    esoc02_novaValidade = fields.Many2one(
        "esoc.02.evttablotac.tperiodovalidade",
        string="Novo período de validade das informações")


class ESocial(spec_models.AbstractSpecMixin):
    _description = 'esocial'
    _name = 'esoc.02.evttablotac.esocial'
    _generateds_type = 'eSocial'
    _concrete_rec_name = 'esoc_evtTabLotacao'

    esoc02_evtTabLotacao = fields.Many2one(
        "esoc.02.evttablotac.evttablotacao",
        string="evtTabLotacao",
        xsd_required=True)


class EvtTabLotacao(spec_models.AbstractSpecMixin):
    "Evento Tabela de Lotações"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttablotac.evttablotacao'
    _generateds_type = 'evtTabLotacaoType'
    _concrete_rec_name = 'esoc_Id'

    esoc02_Id = fields.Char(
        string="Id", xsd_required=True)
    esoc02_ideEvento = fields.Many2one(
        "esoc.02.evttablotac.tidecadastro",
        string="Informações de Identificação do Evento",
        xsd_required=True)
    esoc02_ideEmpregador = fields.Many2one(
        "esoc.02.evttablotac.tempregador",
        string="Informações de identificação do empregador",
        xsd_required=True)
    esoc02_infoLotacao = fields.Many2one(
        "esoc.02.evttablotac.infolotacao",
        string="Informações da Lotação",
        xsd_required=True)


class Exclusao(spec_models.AbstractSpecMixin):
    "Exclusão das informações"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttablotac.exclusao'
    _generateds_type = 'exclusaoType'
    _concrete_rec_name = 'esoc_ideLotacao'

    esoc02_ideLotacao = fields.Many2one(
        "esoc.02.evttablotac.tidelotacao",
        string="Identificação da lotação que será excluída",
        xsd_required=True)


class FpasLotacao(spec_models.AbstractSpecMixin):
    "Informações de FPAS e Terceiros relativas à lotação tributária"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttablotac.fpaslotacao'
    _generateds_type = 'fpasLotacaoType'
    _concrete_rec_name = 'esoc_fpas'

    esoc02_fpas = fields.Integer(
        string="fpas", xsd_required=True)
    esoc02_codTercs = fields.Char(
        string="codTercs", xsd_required=True)
    esoc02_codTercsSusp = fields.Char(
        string="codTercsSusp")
    esoc02_infoProcJudTerceiros = fields.Many2one(
        "esoc.02.evttablotac.infoprocjudterceiros",
        string="infoProcJudTerceiros",
        help="Informações de processos judiciais relativos às contribuições"
        "\ndestinadas a outras Entidades")


class Inclusao(spec_models.AbstractSpecMixin):
    "Inclusão de novas informações"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttablotac.inclusao'
    _generateds_type = 'inclusaoType'
    _concrete_rec_name = 'esoc_ideLotacao'

    esoc02_ideLotacao = fields.Many2one(
        "esoc.02.evttablotac.tidelotacao",
        string="Identificação da Lotação",
        xsd_required=True)
    esoc02_dadosLotacao = fields.Many2one(
        "esoc.02.evttablotac.tdadoslotacao",
        string="Informações da Lotação",
        xsd_required=True)


class InfoEmprParcial(spec_models.AbstractSpecMixin):
    "Informação complementar de obra de construção civil"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttablotac.infoemprparcial'
    _generateds_type = 'infoEmprParcialType'
    _concrete_rec_name = 'esoc_tpInscContrat'

    esoc02_tpInscContrat = fields.Boolean(
        string="tpInscContrat",
        xsd_required=True)
    esoc02_nrInscContrat = fields.Char(
        string="nrInscContrat",
        xsd_required=True)
    esoc02_tpInscProp = fields.Boolean(
        string="tpInscProp", xsd_required=True)
    esoc02_nrInscProp = fields.Char(
        string="nrInscProp", xsd_required=True)


class InfoLotacao(spec_models.AbstractSpecMixin):
    "Informações da Lotação"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttablotac.infolotacao'
    _generateds_type = 'infoLotacaoType'
    _concrete_rec_name = 'esoc_inclusao'

    esoc02_choice1 = fields.Selection([
        ('esoc02_inclusao', 'inclusao'),
        ('esoc02_alteracao', 'alteracao'),
        ('esoc02_exclusao', 'exclusao')],
        "inclusao/alteracao/exclusao",
        default="esoc02_inclusao")
    esoc02_inclusao = fields.Many2one(
        "esoc.02.evttablotac.inclusao",
        choice='1',
        string="Inclusão de novas informações",
        xsd_required=True)
    esoc02_alteracao = fields.Many2one(
        "esoc.02.evttablotac.alteracao",
        choice='1',
        string="Alteração das informações",
        xsd_required=True)
    esoc02_exclusao = fields.Many2one(
        "esoc.02.evttablotac.exclusao",
        choice='1',
        string="Exclusão das informações",
        xsd_required=True)


class InfoProcJudTerceiros(spec_models.AbstractSpecMixin):
    """Informações de processos judiciais relativos às contribuições destinadas
    a outras Entidades"""
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttablotac.infoprocjudterceiros'
    _generateds_type = 'infoProcJudTerceirosType'
    _concrete_rec_name = 'esoc_procJudTerceiro'

    esoc02_procJudTerceiro = fields.One2many(
        "esoc.02.evttablotac.procjudterceiro",
        "esoc02_procJudTerceiro_infoProcJudTerceiros_id",
        string="Identificação do Processo Judicial",
        xsd_required=True
    )


class ProcJudTerceiro(spec_models.AbstractSpecMixin):
    "Identificação do Processo Judicial"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttablotac.procjudterceiro'
    _generateds_type = 'procJudTerceiroType'
    _concrete_rec_name = 'esoc_codTerc'

    esoc02_procJudTerceiro_infoProcJudTerceiros_id = fields.Many2one(
        "esoc.02.evttablotac.infoprocjudterceiros")
    esoc02_codTerc = fields.Char(
        string="codTerc", xsd_required=True)
    esoc02_nrProcJud = fields.Char(
        string="nrProcJud", xsd_required=True)
    esoc02_codSusp = fields.Integer(
        string="codSusp", xsd_required=True)

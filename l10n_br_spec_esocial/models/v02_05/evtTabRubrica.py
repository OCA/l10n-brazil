# Copyright 2019 Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).
# Generated Fri Mar 29 03:16:50 2019 by generateDS.py(Akretion's branch).
# Python 3.6.7 (default, Oct 22 2018, 11:32:17)  [GCC 8.2.0]
#
import textwrap
from odoo import fields
from .. import spec_models


class TDadosRubrica(spec_models.AbstractSpecMixin):
    "Informações da Rubrica"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttabrubri.tdadosrubrica'
    _generateds_type = 'TDadosRubrica'
    _concrete_rec_name = 'esoc_dscRubr'

    esoc02_dscRubr = fields.Char(
        string="dscRubr", xsd_required=True)
    esoc02_natRubr = fields.Integer(
        string="natRubr", xsd_required=True)
    esoc02_tpRubr = fields.Boolean(
        string="tpRubr", xsd_required=True)
    esoc02_codIncCP = fields.Char(
        string="codIncCP", xsd_required=True)
    esoc02_codIncIRRF = fields.Char(
        string="codIncIRRF", xsd_required=True)
    esoc02_codIncFGTS = fields.Char(
        string="codIncFGTS", xsd_required=True)
    esoc02_codIncSIND = fields.Char(
        string="codIncSIND", xsd_required=True)
    esoc02_observacao = fields.Char(
        string="observacao")
    esoc02_ideProcessoCP = fields.One2many(
        "esoc.02.evttabrubri.ideprocessocp",
        "esoc02_ideProcessoCP_TDadosRubrica_id",
        string="Identificação de Processo",
        help="Identificação de Processo - Incidência de Contrib."
        "\nPrevidenciária"
    )
    esoc02_ideProcessoIRRF = fields.One2many(
        "esoc.02.evttabrubri.ideprocessoirrf",
        "esoc02_ideProcessoIRRF_TDadosRubrica_id",
        string="Identificação de Processo",
        help="Identificação de Processo - Incidência de IRRF"
    )
    esoc02_ideProcessoFGTS = fields.One2many(
        "esoc.02.evttabrubri.ideprocessofgts",
        "esoc02_ideProcessoFGTS_TDadosRubrica_id",
        string="Identificação de Processo",
        help="Identificação de Processo - Incidência de FGTS"
    )
    esoc02_ideProcessoSIND = fields.One2many(
        "esoc.02.evttabrubri.ideprocessosind",
        "esoc02_ideProcessoSIND_TDadosRubrica_id",
        string="Identificação de Processo",
        help="Identificação de Processo - Incidência de Contrib. Sindical"
    )


class TEmpregador(spec_models.AbstractSpecMixin):
    _description = 'tempregador'
    _name = 'esoc.02.evttabrubri.tempregador'
    _generateds_type = 'TEmpregador'
    _concrete_rec_name = 'esoc_tpInsc'

    esoc02_tpInsc = fields.Boolean(
        string="tpInsc", xsd_required=True)
    esoc02_nrInsc = fields.Char(
        string="nrInsc", xsd_required=True)


class TIdeCadastro(spec_models.AbstractSpecMixin):
    "Identificação de evento de cadastro/tabelas"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttabrubri.tidecadastro'
    _generateds_type = 'TIdeCadastro'
    _concrete_rec_name = 'esoc_tpAmb'

    esoc02_tpAmb = fields.Boolean(
        string="tpAmb", xsd_required=True)
    esoc02_procEmi = fields.Boolean(
        string="procEmi", xsd_required=True)
    esoc02_verProc = fields.Char(
        string="verProc", xsd_required=True)


class TIdeRubrica(spec_models.AbstractSpecMixin):
    "Identificação da Rubrica e período de validade"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttabrubri.tiderubrica'
    _generateds_type = 'TIdeRubrica'
    _concrete_rec_name = 'esoc_codRubr'

    esoc02_codRubr = fields.Char(
        string="codRubr", xsd_required=True)
    esoc02_ideTabRubr = fields.Char(
        string="ideTabRubr", xsd_required=True)
    esoc02_iniValid = fields.Char(
        string="iniValid", xsd_required=True)
    esoc02_fimValid = fields.Char(
        string="fimValid")


class TPeriodoValidade(spec_models.AbstractSpecMixin):
    "Período de validade das informações"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttabrubri.tperiodovalidade'
    _generateds_type = 'TPeriodoValidade'
    _concrete_rec_name = 'esoc_iniValid'

    esoc02_iniValid = fields.Char(
        string="iniValid", xsd_required=True)
    esoc02_fimValid = fields.Char(
        string="fimValid")


class Alteracao(spec_models.AbstractSpecMixin):
    "Alteração das informações"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttabrubri.alteracao'
    _generateds_type = 'alteracaoType'
    _concrete_rec_name = 'esoc_ideRubrica'

    esoc02_ideRubrica = fields.Many2one(
        "esoc.02.evttabrubri.tiderubrica",
        string="Informações de identificação da rubrica",
        xsd_required=True)
    esoc02_dadosRubrica = fields.Many2one(
        "esoc.02.evttabrubri.tdadosrubrica",
        string="Informações da rubrica",
        xsd_required=True)
    esoc02_novaValidade = fields.Many2one(
        "esoc.02.evttabrubri.tperiodovalidade",
        string="Novo período de validade das informações")


class ESocial(spec_models.AbstractSpecMixin):
    _description = 'esocial'
    _name = 'esoc.02.evttabrubri.esocial'
    _generateds_type = 'eSocial'
    _concrete_rec_name = 'esoc_evtTabRubrica'

    esoc02_evtTabRubrica = fields.Many2one(
        "esoc.02.evttabrubri.evttabrubrica",
        string="evtTabRubrica",
        xsd_required=True)


class EvtTabRubrica(spec_models.AbstractSpecMixin):
    "Evento Tabela de Rubricas"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttabrubri.evttabrubrica'
    _generateds_type = 'evtTabRubricaType'
    _concrete_rec_name = 'esoc_Id'

    esoc02_Id = fields.Char(
        string="Id", xsd_required=True)
    esoc02_ideEvento = fields.Many2one(
        "esoc.02.evttabrubri.tidecadastro",
        string="Informações de Identificação do Evento",
        xsd_required=True)
    esoc02_ideEmpregador = fields.Many2one(
        "esoc.02.evttabrubri.tempregador",
        string="Informações de identificação do empregador",
        xsd_required=True)
    esoc02_infoRubrica = fields.Many2one(
        "esoc.02.evttabrubri.inforubrica",
        string="Informações da Rubrica",
        xsd_required=True)


class Exclusao(spec_models.AbstractSpecMixin):
    "Exclusão das informações"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttabrubri.exclusao'
    _generateds_type = 'exclusaoType'
    _concrete_rec_name = 'esoc_ideRubrica'

    esoc02_ideRubrica = fields.Many2one(
        "esoc.02.evttabrubri.tiderubrica",
        string="Identificação da rubrica que será excluída",
        xsd_required=True)


class IdeProcessoCP(spec_models.AbstractSpecMixin):
    "Identificação de Processo - Incidência de Contrib. Previdenciária"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttabrubri.ideprocessocp'
    _generateds_type = 'ideProcessoCPType'
    _concrete_rec_name = 'esoc_tpProc'

    esoc02_ideProcessoCP_TDadosRubrica_id = fields.Many2one(
        "esoc.02.evttabrubri.tdadosrubrica")
    esoc02_tpProc = fields.Boolean(
        string="tpProc", xsd_required=True)
    esoc02_nrProc = fields.Char(
        string="nrProc", xsd_required=True)
    esoc02_extDecisao = fields.Boolean(
        string="extDecisao", xsd_required=True)
    esoc02_codSusp = fields.Integer(
        string="codSusp", xsd_required=True)


class IdeProcessoFGTS(spec_models.AbstractSpecMixin):
    "Identificação de Processo - Incidência de FGTS"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttabrubri.ideprocessofgts'
    _generateds_type = 'ideProcessoFGTSType'
    _concrete_rec_name = 'esoc_nrProc'

    esoc02_ideProcessoFGTS_TDadosRubrica_id = fields.Many2one(
        "esoc.02.evttabrubri.tdadosrubrica")
    esoc02_nrProc = fields.Char(
        string="nrProc", xsd_required=True)


class IdeProcessoIRRF(spec_models.AbstractSpecMixin):
    "Identificação de Processo - Incidência de IRRF"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttabrubri.ideprocessoirrf'
    _generateds_type = 'ideProcessoIRRFType'
    _concrete_rec_name = 'esoc_nrProc'

    esoc02_ideProcessoIRRF_TDadosRubrica_id = fields.Many2one(
        "esoc.02.evttabrubri.tdadosrubrica")
    esoc02_nrProc = fields.Char(
        string="nrProc", xsd_required=True)
    esoc02_codSusp = fields.Integer(
        string="codSusp", xsd_required=True)


class IdeProcessoSIND(spec_models.AbstractSpecMixin):
    "Identificação de Processo - Incidência de Contrib. Sindical"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttabrubri.ideprocessosind'
    _generateds_type = 'ideProcessoSINDType'
    _concrete_rec_name = 'esoc_nrProc'

    esoc02_ideProcessoSIND_TDadosRubrica_id = fields.Many2one(
        "esoc.02.evttabrubri.tdadosrubrica")
    esoc02_nrProc = fields.Char(
        string="nrProc", xsd_required=True)


class Inclusao(spec_models.AbstractSpecMixin):
    "Inclusão de novas informações"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttabrubri.inclusao'
    _generateds_type = 'inclusaoType'
    _concrete_rec_name = 'esoc_ideRubrica'

    esoc02_ideRubrica = fields.Many2one(
        "esoc.02.evttabrubri.tiderubrica",
        string="ideRubrica", xsd_required=True,
        help="Informações de identificação da rubrica e validade das"
        "\ninformações")
    esoc02_dadosRubrica = fields.Many2one(
        "esoc.02.evttabrubri.tdadosrubrica",
        string="Informações da rubrica",
        xsd_required=True)


class InfoRubrica(spec_models.AbstractSpecMixin):
    "Informações da Rubrica"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttabrubri.inforubrica'
    _generateds_type = 'infoRubricaType'
    _concrete_rec_name = 'esoc_inclusao'

    esoc02_choice1 = fields.Selection([
        ('esoc02_inclusao', 'inclusao'),
        ('esoc02_alteracao', 'alteracao'),
        ('esoc02_exclusao', 'exclusao')],
        "inclusao/alteracao/exclusao",
        default="esoc02_inclusao")
    esoc02_inclusao = fields.Many2one(
        "esoc.02.evttabrubri.inclusao",
        choice='1',
        string="Inclusão de novas informações",
        xsd_required=True)
    esoc02_alteracao = fields.Many2one(
        "esoc.02.evttabrubri.alteracao",
        choice='1',
        string="Alteração das informações",
        xsd_required=True)
    esoc02_exclusao = fields.Many2one(
        "esoc.02.evttabrubri.exclusao",
        choice='1',
        string="Exclusão das informações",
        xsd_required=True)

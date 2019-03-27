# Copyright 2019 Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).
# Generated Fri Mar 29 03:16:47 2019 by generateDS.py(Akretion's branch).
# Python 3.6.7 (default, Oct 22 2018, 11:32:17)  [GCC 8.2.0]
#
import textwrap
from odoo import fields
from .. import spec_models


class TDadosHorContratual(spec_models.AbstractSpecMixin):
    "Informações do Horário Contratual"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttabhortu.tdadoshorcontratual'
    _generateds_type = 'TDadosHorContratual'
    _concrete_rec_name = 'esoc_hrEntr'

    esoc02_hrEntr = fields.Char(
        string="hrEntr", xsd_required=True)
    esoc02_hrSaida = fields.Char(
        string="hrSaida", xsd_required=True)
    esoc02_durJornada = fields.Integer(
        string="durJornada", xsd_required=True)
    esoc02_perHorFlexivel = fields.Char(
        string="perHorFlexivel",
        xsd_required=True)
    esoc02_horarioIntervalo = fields.One2many(
        "esoc.02.evttabhortu.horariointervalo",
        "esoc02_horarioIntervalo_TDadosHorContratual_id",
        string="Intervalos da Jornada definidos no horário contratual"
    )


class TEmpregador(spec_models.AbstractSpecMixin):
    _description = 'tempregador'
    _name = 'esoc.02.evttabhortu.tempregador'
    _generateds_type = 'TEmpregador'
    _concrete_rec_name = 'esoc_tpInsc'

    esoc02_tpInsc = fields.Boolean(
        string="tpInsc", xsd_required=True)
    esoc02_nrInsc = fields.Char(
        string="nrInsc", xsd_required=True)


class TIdeCadastro(spec_models.AbstractSpecMixin):
    "Identificação de evento de cadastro/tabelas"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttabhortu.tidecadastro'
    _generateds_type = 'TIdeCadastro'
    _concrete_rec_name = 'esoc_tpAmb'

    esoc02_tpAmb = fields.Boolean(
        string="tpAmb", xsd_required=True)
    esoc02_procEmi = fields.Boolean(
        string="procEmi", xsd_required=True)
    esoc02_verProc = fields.Char(
        string="verProc", xsd_required=True)


class TIdeHorContratual(spec_models.AbstractSpecMixin):
    "Informações de identificação do Horário Contratual"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttabhortu.tidehorcontratual'
    _generateds_type = 'TIdeHorContratual'
    _concrete_rec_name = 'esoc_codHorContrat'

    esoc02_codHorContrat = fields.Char(
        string="codHorContrat",
        xsd_required=True)
    esoc02_iniValid = fields.Char(
        string="iniValid", xsd_required=True)
    esoc02_fimValid = fields.Char(
        string="fimValid")


class TPeriodoValidade(spec_models.AbstractSpecMixin):
    "Período de validade das informações"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttabhortu.tperiodovalidade'
    _generateds_type = 'TPeriodoValidade'
    _concrete_rec_name = 'esoc_iniValid'

    esoc02_iniValid = fields.Char(
        string="iniValid", xsd_required=True)
    esoc02_fimValid = fields.Char(
        string="fimValid")


class Alteracao(spec_models.AbstractSpecMixin):
    "Alteração das informações"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttabhortu.alteracao'
    _generateds_type = 'alteracaoType'
    _concrete_rec_name = 'esoc_ideHorContratual'

    esoc02_ideHorContratual = fields.Many2one(
        "esoc.02.evttabhortu.tidehorcontratual",
        string="Informações de identificação do horário contratual",
        xsd_required=True)
    esoc02_dadosHorContratual = fields.Many2one(
        "esoc.02.evttabhortu.tdadoshorcontratual",
        string="Informações do horário contratual",
        xsd_required=True)
    esoc02_novaValidade = fields.Many2one(
        "esoc.02.evttabhortu.tperiodovalidade",
        string="Novo período de validade das informações")


class ESocial(spec_models.AbstractSpecMixin):
    _description = 'esocial'
    _name = 'esoc.02.evttabhortu.esocial'
    _generateds_type = 'eSocial'
    _concrete_rec_name = 'esoc_evtTabHorTur'

    esoc02_evtTabHorTur = fields.Many2one(
        "esoc.02.evttabhortu.evttabhortur",
        string="evtTabHorTur",
        xsd_required=True)


class EvtTabHorTur(spec_models.AbstractSpecMixin):
    "Evento Tabela de Horários/Turnos de Trabalho"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttabhortu.evttabhortur'
    _generateds_type = 'evtTabHorTurType'
    _concrete_rec_name = 'esoc_Id'

    esoc02_Id = fields.Char(
        string="Id", xsd_required=True)
    esoc02_ideEvento = fields.Many2one(
        "esoc.02.evttabhortu.tidecadastro",
        string="Informações de Identificação do Evento",
        xsd_required=True)
    esoc02_ideEmpregador = fields.Many2one(
        "esoc.02.evttabhortu.tempregador",
        string="Informações de identificação do empregador",
        xsd_required=True)
    esoc02_infoHorContratual = fields.Many2one(
        "esoc.02.evttabhortu.infohorcontratual",
        string="Informações do horário contratual",
        xsd_required=True)


class Exclusao(spec_models.AbstractSpecMixin):
    "Exclusão das informações"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttabhortu.exclusao'
    _generateds_type = 'exclusaoType'
    _concrete_rec_name = 'esoc_ideHorContratual'

    esoc02_ideHorContratual = fields.Many2one(
        "esoc.02.evttabhortu.tidehorcontratual",
        string="Identificação do horário contratual que será excluído",
        xsd_required=True)


class HorarioIntervalo(spec_models.AbstractSpecMixin):
    "Intervalos da Jornada definidos no horário contratual"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttabhortu.horariointervalo'
    _generateds_type = 'horarioIntervaloType'
    _concrete_rec_name = 'esoc_tpInterv'

    esoc02_horarioIntervalo_TDadosHorContratual_id = fields.Many2one(
        "esoc.02.evttabhortu.tdadoshorcontratual")
    esoc02_tpInterv = fields.Boolean(
        string="tpInterv", xsd_required=True)
    esoc02_durInterv = fields.Integer(
        string="durInterv", xsd_required=True)
    esoc02_iniInterv = fields.Char(
        string="iniInterv")
    esoc02_termInterv = fields.Char(
        string="termInterv")


class Inclusao(spec_models.AbstractSpecMixin):
    "Inclusão de novas informações"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttabhortu.inclusao'
    _generateds_type = 'inclusaoType'
    _concrete_rec_name = 'esoc_ideHorContratual'

    esoc02_ideHorContratual = fields.Many2one(
        "esoc.02.evttabhortu.tidehorcontratual",
        string="Identificação da Horário Contratual",
        xsd_required=True)
    esoc02_dadosHorContratual = fields.Many2one(
        "esoc.02.evttabhortu.tdadoshorcontratual",
        string="Informações do horário contratual",
        xsd_required=True)


class InfoHorContratual(spec_models.AbstractSpecMixin):
    "Informações do horário contratual"
    _description = textwrap.dedent("    %s" % (__doc__,))
    _name = 'esoc.02.evttabhortu.infohorcontratual'
    _generateds_type = 'infoHorContratualType'
    _concrete_rec_name = 'esoc_inclusao'

    esoc02_choice1 = fields.Selection([
        ('esoc02_inclusao', 'inclusao'),
        ('esoc02_alteracao', 'alteracao'),
        ('esoc02_exclusao', 'exclusao')],
        "inclusao/alteracao/exclusao",
        default="esoc02_inclusao")
    esoc02_inclusao = fields.Many2one(
        "esoc.02.evttabhortu.inclusao",
        choice='1',
        string="Inclusão de novas informações",
        xsd_required=True)
    esoc02_alteracao = fields.Many2one(
        "esoc.02.evttabhortu.alteracao",
        choice='1',
        string="Alteração das informações",
        xsd_required=True)
    esoc02_exclusao = fields.Many2one(
        "esoc.02.evttabhortu.exclusao",
        choice='1',
        string="Exclusão das informações",
        xsd_required=True)

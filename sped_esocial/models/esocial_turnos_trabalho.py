# -*- coding: utf-8 -*-
# Copyright 2018 ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from dateutil import relativedelta

from openerp import api, models, fields
from openerp.exceptions import Warning


class SpedEsocialTurnosTrabalho(models.Model):
    _name = "esocial.turnos.trabalho"

    @api.multi
    def _get_periodo_atual_default(self):
        periodo_atual = fields.Datetime.from_string(fields.Datetime.now())

        return "{}-{:0>2}".format(periodo_atual.year, periodo_atual.month)

    name = fields.Char(
        compute="_get_display_name",
    )

    hr_entr = fields.Char(
        string="Horário de Entrada",
        required=True,
        size=5,
    )
    hr_saida = fields.Char(
        string="Horário de Saída",
        required=True,
        size=5,
    )
    horario_intervalo_ids = fields.Many2many(
        string="Intervalos",
        comodel_name="sped.esocial.turnos.intervalo",
        column1='turno_trabalho_id',
        column2='intervalo_id',
    )
    dur_jornada = fields.Char(
        string="Tempo de Duração",
        compute="_calcular_tempo_duracao_turno"
    )
    per_hor_flexivel = fields.Selection(
        string="Permite Flexibilidade?",
        selection=[
            ('S', 'Sim'),
            ('N', 'Não'),
        ]
    )
    cod_hor_contrat = fields.Char(
        string="Código no e-Social",
        required=True,
        size=30,
    )
    ini_valid = fields.Char(
        string="Competência de início",
        required=True,
        size=7,
        default=_get_periodo_atual_default,
    )
    fim_valid = fields.Char(
        string="Competência final",
        size=7,
    )
    sped_esocial_turnos_trabalho_ids = fields.One2many(
        comodel_name="sped.esocial.turnos.trabalho",
        inverse_name="sped_esocial_turnos_trabalho_id"
    )

    @api.multi
    def _get_display_name(self):
        for record in self:
            name = "Turno: {} até {}".format(record.hr_entr, record.hr_saida)
            record.name = name

    @api.multi
    def _calcular_tempo_duracao_turno(self):
        for record in self:
            hora_entrada = fields.Datetime.from_string(
                '2018-01-01 {}:{}:00'.format(
                    record.hr_entr[:2], record.hr_entr[3:]
                )
            )
            hora_saida = fields.Datetime.from_string(
                '2018-01-01 {}:{}:00'.format(
                    record.hr_saida[:2], record.hr_saida[3:]
                )
            )
            diferencas = relativedelta.relativedelta(
                hora_saida, hora_entrada,
            )
            record.dur_jornada = (diferencas.hours * 60) + diferencas.minutes

    @api.multi
    def gerar_documento_sped(self):
        """
        
        :return: 
        """
        sped_turnos_obj = self.env['sped.esocial.turnos.trabalho']
        sped_esocial_obj = self.env['sped.esocial']
        company_id = self.env['res.company'].search([
            ('eh_empresa_base', '=', True),
        ], limit=1)
        sped_esocial_id = sped_esocial_obj.get_esocial_vigente(company_id)

        sped_turnos_obj.create({
            'esocial_id': sped_esocial_id.id,
            'sped_esocial_turnos_trabalho_id': self.id,
        })

    @api.model
    def create(self, vals):
        self._validacoes_campos_turno(vals)
        return super(SpedEsocialTurnosTrabalho, self).create(vals)

    @api.multi
    def write(self, vals):
        self._validacoes_campos_turno(vals)
        return super(SpedEsocialTurnosTrabalho, self).write(vals)

    @api.multi
    def _validacoes_campos_turno(self, vals):
        self._validar_campos_horas(vals)
        self._validar_campos_periodo(vals)

    @api.multi
    def _validar_campos_horas(self, vals):
        if vals.get('hr_entr'):
            self._validar_formato_campo_hora(vals.get('hr_entr'))
        if vals.get('hr_saida'):
            self._validar_formato_campo_hora(vals.get('hr_saida'))

    @api.multi
    def _validar_formato_campo_hora(self, hora_minuto):
        if not hora_minuto[2] == ':':
            raise Warning(
                "Formato do campo hora está incorreto, "
                "o modelo correto é no formato 'HH:MM'!"
            )

        hora = int(hora_minuto[:2])
        if hora < 0 or hora > 23:
            raise Warning(
                "Hora deve estar entre 00 e 23!"
            )

        minuto = int(hora_minuto[3:])
        if minuto < 0 or minuto > 59:
            raise Warning(
                "Minuto deve estar entre 00 e 59!"
            )

    @api.multi
    def _validar_campos_periodo(self, vals):
        if vals.get('ini_valid'):
            self._validar_formato_campo_periodo(vals.get('ini_valid'))
        if vals.get('fim_valid'):
            self._validar_formato_campo_periodo(vals.get('fim_valid'))

    @api.multi
    def _validar_formato_campo_periodo(self, periodo):
        if not periodo[4] == '-':
            raise Warning(
                "Formato do campo periodo está incorreto, "
                "o modelo correto é AAAA-MM!"
            )
        mes = int(periodo[5:])
        if mes < 1 or mes > 12:
            raise Warning(
                "Mês deve estar entre 1 e 12!"
            )


class SpedEsocialTurnosIntervalo(models.Model):
    _name = "sped.esocial.turnos.intervalo"

    ini_interv = fields.Char(
        string="Horário de Início",
        required=True,
        size=5
    )
    term_interv = fields.Char(
        string="Horário de Fim",
        required=True,
        size=5
    )
    dur_interv = fields.Char(
        string="Duração",
        compute="_calcular_tempo_duracao_intervalo"
    )
    tp_interv = fields.Selection(
        string="Tipo de intervalo",
        selection=[
            ('1', 'Intervalo em horário fixo'),
            ('2', 'Intervalo em horário variável'),
        ]
    )

    @api.multi
    def _calcular_tempo_duracao_intervalo(self):
        for record in self:
            hora_entrada = fields.Datetime.from_string(
                '2018-01-01 {}:{}:00'.format(
                    record.ini_interv[:2], record.ini_interv[3:]
                )
            )
            hora_saida = fields.Datetime.from_string(
                '2018-01-01 {}:{}:00'.format(
                    record.term_interv[:2], record.term_interv[3:]
                )
            )
            diferencas = relativedelta.relativedelta(
                hora_saida, hora_entrada,
            )
            record.dur_interv = (diferencas.hours * 60) + diferencas.minutes

    @api.model
    def create(self, vals):
        self._validacoes_campos_turno(vals)

    @api.multi
    def _validacoes_campos_turno(self, vals):
        self._validar_campos_horas(vals)

    @api.multi
    def _validar_campos_horas(self, vals):
        if vals.get('ini_interv'):
            self.sped_esocial_turnos_trabalho_id._validar_formato_campo_hora(
                vals.get('ini_interv')
            )
        if vals.get('term_interv'):
            self.sped_esocial_turnos_trabalho_id._validar_formato_campo_hora(
                vals.get('term_interv')
            )

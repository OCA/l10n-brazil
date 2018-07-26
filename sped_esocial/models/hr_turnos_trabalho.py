# -*- coding: utf-8 -*-
# Copyright 2018 ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from dateutil import relativedelta

from openerp import api, models, fields
from openerp.exceptions import Warning


class SpedEsocialTurnosTrabalho(models.Model):
    _name = "hr.turnos.trabalho"

    # Campos de controle S-1050
    sped_turno_id = fields.Many2one(
        string='SPED Turnos de Trabalho',
        comodel_name='sped.hr.turnos.trabalho',
    )
    situacao_esocial = fields.Selection(
        selection=[
            ('0', 'Inativo'),
            ('1', 'Ativo'),
            ('2', 'Precisa Atualizar'),
            ('3', 'Aguardando Transmissão'),
            ('4', 'Aguardando Processamento'),
            ('5', 'Erro(s)'),
            ('9', 'Finalizado'),
        ],
        string='Situação Turno no e-Social',
        related='sped_turno_id.situacao_esocial',
        readonly=True,
    )
    precisa_atualizar = fields.Boolean(
        string='Precisa Atualizar',
    )

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
        comodel_name="hr.turnos.intervalo",
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
        size=30,
    )
    ini_valid = fields.Many2one(
        string="Competência Inicial",
        comodel_name='account.period',
        domain=lambda self: self._field_id_domain(),
    )
    alt_valid = fields.Many2one(
        string="Alteração válida desde",
        comodel_name='account.period',
        domain=lambda self: self._field_id_domain(),
    )
    fim_valid = fields.Many2one(
        string="Competência Final",
        comodel_name='account.period',
        domain=lambda self: self._field_id_domain(),
    )
    # sped_hr_turnos_trabalho_ids = fields.One2many(
    #     comodel_name="sped.hr.turnos.trabalho",
    #     inverse_name="hr_turnos_trabalho_id"
    # )

    @api.onchange('ini_valid')
    def onchange_esocial_periodo_inicial_id(self):
        self.ensure_one()
        if not self.alt_valid or \
                self.alt_valid.date_start < \
                self.ini_valid.date_start:
            self.alt_valid = self.ini_valid

    @api.multi
    def atualizar_turno(self):
        self.ensure_one()

        # Se o registro intermediário do S-1050 não existe, criá-lo
        if not self.sped_turno_id:

            # Verifica se o registro intermediário já existe
            domain = [
                ('company_id', '=', self.env.user.company_id.id),
                ('hr_turnos_trabalho_id', '=', self.id),
            ]
            sped_turno_id = self.env['sped.hr.turnos.trabalho'].search(domain)
            if sped_turno_id:
                self.sped_turno_id = sped_turno_id
            else:
                self.sped_turno_id = \
                    self.env['sped.hr.turnos.trabalho'].create({
                        'company_id': self.env.user.company_id.id,
                        'hr_turnos_trabalho_id': self.id,
                    })

        # Processa cada tipo de operação do S-1000 (Inclusão / Alteração / Exclusão)
        # O que realmente precisará ser feito é tratado no método do registro intermediário
        self.sped_turno_id.gerar_registro()

    @api.multi
    def write(self, vals):
        self.ensure_one()

        # Lista os campos que são monitorados do Empregador
        campos_monitorados = [
            'ini_valid',                # //eSocial/evtTabHorTur/infoHorContratual//ideHorContratual/iniValid
            'alt_valid',                # //eSocial/evtTabHorTur/infoHorContratual//novaValidade/iniValid
            'hr_entr',                  # //eSocial/evtTabHorTur/infoHorContratual//dadosHorContratual/hrEntr
            'hr_saida',                 # //eSocial/evtTabHorTur/infoHorContratual//dadosHorContratual/hrSaida
            'dur_jornada ',             # //eSocial/evtTabHorTur/infoHorContratual//dadosHorContratual/durJornada
            'per_hor_flexivel',         # //eSocial/evtTabHorTur/infoHorContratual//dadosHorContratual/perHorFlexivel
            'horario_intervalo_ids ',   # //eSocial/evtTabHorTur/infoHorContratual//dadosHorContratual/horarioIntervalo
        ]
        precisa_atualizar = False

        # Roda o vals procurando se algum desses campos está na lista
        # Empregador
        if self.sped_turno_id and self.situacao_esocial == '1':
            for campo in campos_monitorados:
                if campo in vals:
                    precisa_atualizar = True

            # Se precisa_atualizar == True, inclui ele no vals
            if precisa_atualizar:
                vals['precisa_atualizar'] = precisa_atualizar

        self._validacoes_campos_turno(vals)

        # Grava os dados
        return super(SpedEsocialTurnosTrabalho, self).write(vals)

    @api.multi
    def transmitir_turno(self):
        self.ensure_one()

        # Executa o método Transmitir do registro intermediário
        self.sped_turno_id.transmitir()

    @api.multi
    def consultar_turno(self):
        self.ensure_one()

        # Executa o método Consultar do registro intermediário
        self.sped_turno_id.consultar()

    @api.model
    def _field_id_domain(self):
        """
        Dominio para buscar os registros maiores que 01/2017
        """
        domain = [
            ('date_start', '>=', '2017-01-01'),
            ('special', '=', False)
        ]

        return domain

    @api.multi
    def _get_display_name(self):
        for record in self:
            name = "Turno: {} até {}".format(record.hr_entr, record.hr_saida)
            if len(record.horario_intervalo_ids) > 0:
                name += ' Intervalo ('
                primeiro = True
                for intervalo in record.horario_intervalo_ids:
                    if not primeiro:
                        name += ' e '
                    name += intervalo.ini_interv + '-' + intervalo.term_interv
                    primeiro = False
                name += ')'
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

    # @api.multi
    # def gerar_documento_sped(self):
    #     """
    #
    #     :return:
    #     """
    #     hr_turnos_obj = self.env['sped.hr.turnos.trabalho']
    #     sped_esocial_obj = self.env['sped.esocial']
    #     company_id = self.env['res.company'].search([
    #         ('eh_empresa_base', '=', True),
    #     ], limit=1)
    #     sped_esocial_id = sped_esocial_obj.get_esocial_vigente(company_id)
    #
    #     hr_turnos_obj.create({
    #         'esocial_id': sped_esocial_id.id,
    #         'sped_hr_turnos_trabalho_id': self.id,
    #     })

    @api.model
    def create(self, vals):
        self._validacoes_campos_turno(vals)
        return super(SpedEsocialTurnosTrabalho, self).create(vals)

    @api.multi
    def _validacoes_campos_turno(self, vals):
        self._validar_campos_horas(vals)
        # self._validar_campos_periodo(vals)

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

    # @api.multi
    # def atualizar_turno(self):
    #     self.ensure_one()
    #
    #     # Se o registro intermediário do S-1050 não existe, criá-lo
    #     if not self.sped_hr_turnos_trabalho_ids:
    #         if self.env.user.company_id.eh_empresa_base:
    #             matriz = self.env.user.company_id.id
    #         else:
    #             matriz = self.env.user.company_id.matriz.id
    #
    #         self.sped_hr_turnos_trabalho_ids = \
    #             self.env['sped.hr.turnos.trabalho'].create({
    #                 'company_id': matriz,
    #                 'hr_turnos_trabalho_id': self.id,
    #             })
    #
    #     # Processa cada tipo de operação do S-1050 (Inclusão / Alteração / Exclusão)
    #     # O que realmente precisará ser feito é tratado no método do registro intermediário
    #     self.sped_hr_turnos_trabalho_ids.gerar_registro()


class SpedEsocialTurnosIntervalo(models.Model):
    _name = "hr.turnos.intervalo"

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
        return super(SpedEsocialTurnosIntervalo, self).create(vals)

    @api.multi
    def _validacoes_campos_turno(self, vals):
        self._validar_campos_horas(vals)

    @api.multi
    def _validar_campos_horas(self, vals):
        if vals.get('ini_interv'):
            self.env['hr.turnos.trabalho']._validar_formato_campo_hora(
                vals.get('ini_interv')
            )
            # self.sped_hr_turnos_trabalho_id._validar_formato_campo_hora(

        if vals.get('term_interv'):
            self.env['hr.turnos.trabalho']._validar_formato_campo_hora(
                    vals.get('term_interv')
                )

# -*- coding: utf-8 -*-KMEE
# Copyright 2019 ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models, _
import datetime as dt
import pandas as pd


DIAS_SEMANA = ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sab', 'Dom']

MARITAL = {'single': 'Solteiro(a)',
           'married': 'Casado(a)',
           'widower': 'Viuvo(a)',
           'divorced': 'Divorciado(a)',
           'common_law_marriage': 'Common Law Marriage',
           'separated': 'Separado(a)'}


class WizardL10nBrHrEmployeeFichaRegistro(models.TransientModel):
    _name = 'wizard.l10n_br_hr_employee.ficha_registro'

    employee_id = fields.Many2one(
        comodel_name='hr.employee',
        default=lambda self: self._context.get('employee_id'),
        readonly=True,
    )

    contract_id = fields.Many2one(
        comodel_name='hr.contract',
        related='employee_id.contract_id',
    )

    companylogo = fields.Binary(
        string='Logo ABGF',
        compute='_compute_ficha_registro',
    )

    company_cabecalho = fields.Html(
        compute='_compute_ficha_registro',
    )

    image_medium = fields.Binary(
        related='employee_id.image_medium',
        readonly=True,
    )

    name = fields.Char(
        related='employee_id.name',
        readonly=True,
    )

    matricula = fields.Char(
        compute='_compute_ficha_registro',
        readonly=True,
    )

    endereco = fields.Char(
        string=u'Endereço',
        compute='_compute_ficha_registro',
    )

    father_name = fields.Char(
        string=u'Nome do Pai',
        related='employee_id.father_name',
        readonly=True,
    )

    mother_name = fields.Char(
        string=u'Nome da Mãe',
        related='employee_id.mother_name',
        readonly=True,
    )

    birthday = fields.Char(
        string=u'Data Nascimento',
        compute='_compute_ficha_registro',
        readonly=True,
    )

    dependent_ids = fields.One2many(
        string=u'Dependentes',
        comodel_name='hr.employee.dependent',
        related='employee_id.dependent_ids',
    )

    conjuge = fields.Char(
        string=u'Cônjuge',
        compute='_compute_ficha_registro',
    )

    creservist = fields.Char(
        string=u'Reservista',
        related='employee_id.creservist',
        readonly=True,
    )

    titulo_eleitoral = fields.Char(
        string=u'Titulo Eleitoral',
        compute='_compute_ficha_registro',
    )

    dt_opc_fgts = fields.Char(
        string=u'Data da Opção',
        compute='_compute_ficha_registro',
    )

    conjuge_brasileiro = fields.Char(
        string=u'Casado com Brasileiro',
        # compute='_compute_ficha_registro',
    )

    cargo = fields.Char(
        string=u'Cargo',
        compute='_compute_ficha_registro',
        readonly=True,
    )

    blood_type = fields.Char(
        string=u'Tipo Sanguíneo',
        compute='_compute_ficha_registro',
        readonly=True,
    )

    date_start = fields.Char(
        string=u'Data da Admissão',
        compute='_compute_ficha_registro',
    )

    dt_desligamento = fields.Char(
        string=u'Data do desligamento',
        compute='_compute_ficha_registro',
    )

    pis_pasep = fields.Char(
        string=u'PIS/PASEP',
        related='employee_id.pis_pasep',
        readonly=True,
    )

    working_hours = fields.Html(
        string=u'Horário de Trabalho',
        compute='_compute_ficha_registro',
    )

    working_hours_dict = fields.Char(
        string=u'Horário de Trabalho',
        compute='_compute_ficha_registro',
    )

    naturalidade = fields.Char(
        string=u'Naturalidade',
        compute='_compute_ficha_registro',
    )

    identidade = fields.Char(
        string=u'Identidade',
        compute='_compute_ficha_registro',
    )

    ctps = fields.Char(
        string=u'CTPS',
        compute='_compute_ficha_registro',
    )

    cpf = fields.Char(
        string=u'CPF',
        related='employee_id.cpf',
        readonly=True,
    )

    nacionalidade = fields.Char(
        string=u'Nacionalidade',
        compute='_compute_ficha_registro',
    )

    cbo = fields.Char(
        string=u'CBO',
        compute='_compute_ficha_registro',
    )

    estado_civil = fields.Char(
        string=u'Estado Civil',
        compute='_compute_ficha_registro',
        readonly=True,
    )

    educational_attainment = fields.Char(
        string=u'Grau de Instrução',
        compute='_compute_ficha_registro',
    )

    naturalizado = fields.Char(
        string=u'É naturalizado?',
        compute='_compute_ficha_registro',
    )

    forma_pg = fields.Char(
        string=u'Forma de Pagto',
        compute='_compute_ficha_registro',
    )

    wage = fields.Char(
        string=u'Salário',
        compute='_compute_ficha_registro',
    )

    change_salary_ids = fields.Many2many(
        string='Alterações de Salário',
        comodel_name='l10n_br_hr.contract.change',
        relation='ficha_registro_change_salary_ids',
        compute='_compute_ficha_registro',
    )

    change_job_ids = fields.Many2many(
        string='Alterações de Cargo',
        comodel_name='l10n_br_hr.contract.change',
        relation='ficha_registro_change_job_ids',
        compute='_compute_ficha_registro',
    )

    vacation_control_ids = fields.Many2many(
        string='Férias',
        comodel_name='hr.vacation.control',
        relation='ficha_registro_vacation_control_ids',
        compute='_compute_ficha_registro',
    )

    def format_date(self, data):
        if data:
            return dt.datetime.strptime(data, "%Y-%m-%d").strftime("%d/%m/%Y")

    def create_jornada_trabalho_tb(self, contract):
        att_ids = contract.working_hours.attendance_ids

        data = [[DIAS_SEMANA[int(att_id.diadasemana)-1],
                 att_id.turno_id.hr_entr,
                 att_id.turno_id.horario_intervalo_ids.ini_interv,
                 att_id.turno_id.horario_intervalo_ids.term_interv,
                 att_id.turno_id.hr_saida] for att_id in att_ids]
        dias_folga = ','.join(list(set(DIAS_SEMANA) - set(
            [DIAS_SEMANA[int(att.diadasemana)-1] for att in att_ids])))

        jornada = dict()

        for linha in data:
            hours = str(linha[1:])
            if hours not in jornada.keys():
                jornada[hours] = str(linha[0])
            else:
                jornada[hours] = '{}, {}'.format(jornada[hours], linha[0])

        data_df = [(jornada[j], eval(j)[0], eval(j)[1], eval(j)[2], eval(j)[3])
                   for j in jornada]

        data_df.append((dias_folga, '', '', '', ''))

        cols = ['Dia(s)', 'Entrada', 'Início Intervalo', 'Fim Intervalo',
                'Saída']
        df = pd.DataFrame(data=data_df, columns=cols)
        df.set_index('Dia(s)', inplace=True)

        return df.to_html(classes='table table-condensed',
                          border='0'), str(data_df)

    @api.multi
    @api.depends('employee_id', 'dependent_ids')
    def _compute_ficha_registro(self):
        self.ensure_one()
        employee = self.employee_id
        contract = employee.contract_id
        partner = employee.address_home_id
        company = employee.company_id
        # Logo ABGF
        self.companylogo = company.nfe_logo

        # Cabeçalho
        self.company_cabecalho = '<div style="text-align: center; ' \
                                 'margin-top: 10px;">' \
                                 '<h3>{}</h3><p>{}<br />CNPJ: {}</p>' \
                                 '</div>'.\
            format(company.partner_id.legal_name,
                   company.partner_id.contact_address,
                   company.partner_id.cnpj_cpf)

        # Endereço
        self.endereco = u'{} {}{}{} {} - {}/{}'.format(
            partner.tp_lograd.nome, partner.street, ', ' + str(partner.number)
            if partner.number else ' ', ' - ' + partner.street2 + ' - '
            if partner.street2 else '', partner.district,
            partner.l10n_br_city_id.name, partner.state_id.code)

        # Matrícula
        self.matricula = contract.matricula_contrato

        # Data Nascimento
        self.birthday = self.format_date(employee.birthday)

        # Conjuge
        conjuge = self.dependent_ids.filtered(
            lambda x: x.dependent_type_id.name == 'Cônjuge')
        self.conjuge = conjuge.dependent_name

        # Titulo Eleitoral
        self.titulo_eleitoral = u'{} - Zona {} - Seção {} '.format(
            employee.voter_title, employee.voter_zone, employee.voter_section)

        # Data opção FGTS
        self.dt_opc_fgts = self.format_date(contract.dt_opc_fgts)

        # Cargo
        self.cargo = contract.job_id.name

        # Tipo Sanguineo
        self.blood_type = employee.blood_type

        # Data da Admissão
        dt_start = self.format_date(contract.date_start)
        self.date_start = dt_start

        # Data Desligamento
        self.dt_desligamento = self.format_date(contract.resignation_date) \
                               or ''

        # Horário de Trabalho
        self.working_hours, self.working_hours_dict = \
            self.create_jornada_trabalho_tb(contract)
        self.working_hours = self.working_hours.replace(
            'border="0"', 'border="0" style="font-size:11px; '
                          'border-bottom:1px solid #ccc;"')

        # Identidade
        rg_dt = self.format_date(employee.rg_emission)
        self.identidade = u'{}/{} emitida em {}'.format(
            employee.rg, employee.organ_exp, rg_dt)

        # CTPS
        ctps_dt = self.format_date(employee.ctps_date)
        self.ctps = u'Nº: {} | Serie/UF: {}/{} emitida em {}'.format(
            employee.ctps, employee.ctps_series, employee.ctps_uf_id.code,
            ctps_dt)

        # Nacionalidade
        self.nacionalidade = employee.pais_nac_id.name

        # Naturalidade
        self.naturalidade = '{}/{}'.format(employee.naturalidade.name,
                                           employee.naturalidade.state_id.code)

        # Grau de Instrução
        self.educational_attainment = employee.educational_attainment.name

        # É naturalizado
        self.naturalizado = 'Não' if not employee.pais_nac_id.name \
                                     or 'Brasil' in employee.pais_nac_id.name \
                                  else 'Sim'

        # Salário
        self.wage = self.format_money_mask(contract.wage)

        #CBO
        self.cbo = contract.job_id.cbo_id.code

        # Estado Civil
        self.estado_civil = \
            MARITAL[employee.marital] if employee.marital else False

        # Preencher tabelas Many2Many
        self.change_salary_ids = contract.change_salary_ids
        self.change_job_ids = contract.change_job_ids
        self.vacation_control_ids = contract.vacation_control_ids

    def format_money_mask(self, value):
        """
        Function to transform float values to pt_BR currency mask
        :param value: float value
        :return: value with brazilian money format
        """
        import locale
        locale.setlocale(locale.LC_ALL, 'pt_BR.utf8')
        value_formated = locale.currency(value, grouping=True)

        return value_formated[3:]

    @api.multi
    def doit(self, vals):
        super(WizardL10nBrHrEmployeeFichaRegistro, self).create(vals)
        return self.env['report'].get_action(
            self, "l10n_br_hr_payroll_report.report_ficha_registro")

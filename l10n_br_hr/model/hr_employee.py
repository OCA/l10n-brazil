# -*- coding: utf-8 -*-
# (c) 2014 Kmee - Rafael da Silva Lima <rafael.lima@kmee.com.br>
# (c) 2014 Kmee - Matheus Felix <matheus.felix@kmee.com.br>
# (c) 2016 KMEE Informática - Daniel Sadamo <daniel.sadamo@kmee.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import models, fields, api, _
from datetime import datetime
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
from openerp.exceptions import ValidationError


NATIONALITY_CODE = [
    ('10', '10 - Brasileiro'),
    ('20', '20 - Naturalizado Brasileiro'),
    ('21', '21 - Argentino'),
    ('22', '22 - Boliviano'),
    ('23', '23 - Chileno'),
    ('24', '24 - Paraguaio'),
    ('25', '25 - Uruguaio'),
    ('26', '26 - Venezuelano'),
    ('27', '27 - Colombiano'),
    ('28', '28 - Peruano'),
    ('29', '29 - Equatoriano'),
    ('30', u'30 - Alemão'),
    ('31', '31 - Belga'),
    ('32', u'32 - Britânico'),
    ('34', '34 - Canadense'),
    ('35', '35 - Espanhol'),
    ('36', '36 - Norte-americano'),
    ('37', u'37 - Francês'),
    ('38', u'38 - Suíço'),
    ('39', '39 - Italiano'),
    ('40', '40 - Haitiano'),
    ('41', u'41 - Japonês'),
    ('42', u'42 - Chines'),
    ('43', '43 - Coreano'),
    ('44', '44 - Russo'),
    ('45', u'45 - Português'),
    ('46', u'46 - Paquistanês'),
    ('47', '47 - Indiano'),
    ('48', '48 - Outros latino-americanos'),
    ('49', u'49 - Outros asiáticos'),
    ('50', u'50 - Bengalês'),
    ('51', '51 - Outros Europeus'),
    ('60', '60 - Angolano'),
    ('61', u'61 - Congolês'),
    ('62', '62 - Sul-africano'),
    ('63', u'63 - Ganês'),
    ('64', u'64 - Senegalês'),
    ('70', '70 - Outros Africanos'),
    ('80', '80 - Outros')
]


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    @api.constrains('dependent_ids')
    def _check_dependents(self):
        self._check_dob()
        self._check_dependent_type()

    def _check_dob(self):
        for dependent in self.dependent_ids:
            if datetime.strptime(
                    dependent.dependent_dob, DEFAULT_SERVER_DATE_FORMAT
                    ).date() > datetime.now().date():
                raise ValidationError(_(u'Data de nascimento do '
                                        u'dependente %s inválida'
                                        % dependent.dependent_name))

    def _check_dependent_type(self):
        seen = set()
        for dependent in self.dependent_ids:
            dep_type = dependent.dependent_type_id
            if dep_type not in seen and dep_type.code in (1, 9):
                seen.add(dep_type)
            elif dep_type in seen and dep_type.code in (1, 9):
                raise ValidationError(
                    _(u'Já existe um dependente com o mesmo grau '
                      u'de parentesco de %s'
                      % dependent.dependent_name))

    @api.constrains('pis_pasep')
    def _validate_pis_pasep(self):
        employee = self
        if not employee.pis_pasep:
            return True
        digits = []
        for c in employee.pis_pasep:
            if c == '.' or c == ' ' or c == '\t':
                continue
            if c == '-':
                if len(digits) != 10:
                    raise ValidationError(_(u'PIS/PASEP inválido'))
                continue
            if c.isdigit():
                digits.append(int(c))
                continue
            raise ValidationError(_(u'PIS/PASEP inválido'))
        if len(digits) != 11:
            raise ValidationError(_(u'PIS/PASEP inválido'))
        height = [int(x) for x in "3298765432"]
        total = 0
        for i in range(10):
            total += digits[i] * height[i]
        rest = total % 11
        if rest != 0:
            rest = 11 - rest
        if not rest == digits[10]:
            raise ValidationError(_(u'PIS/PASEP inválido'))

    check_cpf = fields.Boolean('Verificar CPF', default=True)
    pis_pasep = fields.Char(u'PIS/PASEP', size=15)
    ctps = fields.Char('CTPS', help=u'Número do CTPS')
    ctps_series = fields.Char('Série')
    ctps_date = fields.Date(u'Data de emissão')
    ctps_uf_id = fields.Many2one(string='UF da CTPS',
                                 comodel_name='res.country.state')
    creservist = fields.Char('Título de reservista')
    cresv_categ = fields.Selection(string='Categoria de reservista',
                                   selection=[
                                       ('1', 'Primeira Categoria'),
                                       ('2', 'Segunda Categoria'),
                                       ('3', 'Terceira Categoria')])
    ginstru = fields.Selection(
        string=u'Grau de instrução',
        selection=[
            ('fundamental_incompleto', 'Fundamental incompleto'),
            ('fundamental', 'Fundamental completo'),
            ('medio_incompleto', u'Ensino médio incompleto'),
            ('medio', u'Ensino médio completo'),
            ('superior_incompleto', 'Superior incompleto'),
            ('superior', 'Superior completo'),
            ('mestrado', 'Mestrado'),
            ('doutorado', 'Doutorado')
        ])
    have_dependent = fields.Boolean('Possui dependentes')
    dependent_ids = fields.One2many(comodel_name='hr.employee.dependent',
                                    inverse_name='employee_id',
                                    string='Dependentes')
    rg = fields.Char(string='RG', help=u'Número do RG')
    cpf = fields.Char(string='CPF', related='address_home_id.cnpj_cpf',
                      required=True)
    organ_exp = fields.Char(string=u'Órgão expeditor')
    rg_emission = fields.Date(string='Data de emissão')
    voter_title = fields.Char(string=u'Título de eleitor')
    voter_zone = fields.Char(string='Zona de votação')
    voter_section = fields.Char(string=u'Seção de votação')
    driver_license = fields.Char(string=u'Número da CNH')
    driver_categ = fields.Char(string=u'Categoria de habilitação')
    father_name = fields.Char(string=u'Nome do pai')
    mother_name = fields.Char(string=u'Nome da mãe')
    expiration_date = fields.Date(string=u'Validade')
    sindicate = fields.Char(string=u'Sindicato', help=u'Sigla do sindicato')
    ethnicity = fields.Selection(string=u'Raça/Cor', selection=[
        ('indigena', u'Indígena'),
        ('branca', 'Branco'),
        ('negra', 'Negro'),
        ('amarela', 'Amarelo'),
        ('parda', 'Pardo'),
        ('nao_informada', u'Não Informado')
    ])
    blood_type = fields.Selection(string=u'Tipo sanguíneo', selection=[
        ('a+', 'A+'),
        ('a-', 'A-'),
        ('b+', 'B+'),
        ('b-', 'B-'),
        ('o+', 'O+'),
        ('o-', 'O-'),
        ('ab+', 'AB+'),
        ('ab-', 'AB-'),
    ])
    deficiencies_ids = fields.Many2many(string=u'Deficiências',
                                        comodel_name='hr.deficiency')
    identity_type_id = fields.Many2one(string='Tipo de identidade',
                                       comodel_name='hr.identity.type')
    identity_validity = fields.Date(string='Validade da identidade')
    identity_uf_id = fields.Many2one(string='UF da identidade',
                                     comodel_name='res.country.state')
    identity_city_id = fields.Many2one(
        string=u'Município da identidade',
        comodel_name='l10n_br_base.city',
        domain="[('state_id','=',identity_uf_id)]")
    civil_certificate_type_id = fields.Many2one(
        string=u'Tipo de certidão civil',
        comodel_name='hr.civil.certificate.type')
    alternate_phone = fields.Char(string='Telefone alternativo')
    emergency_phone = fields.Char(string=u'Telefone de emergência')
    talk_to = fields.Char(string='Falar com')
    alternate_email = fields.Char(string='Email alternativo')
    chronic_disease_ids = fields.Many2many(string=u'Doenças Crônicas',
                                           comodel_name='hr.chronic.disease')
    admission_date = fields.Date(string=u'Data de admissão')
    marital = fields.Selection(selection_add=[
        ('stable_union', u'União Estável'), ('separado', 'Separado')])
    registration = fields.Char(string=u'Matrícula')
    nationality_code = fields.Selection(string=u'Código de nacionalidade',
                                        selection=NATIONALITY_CODE)
    arrival_year = fields.Integer(string="Ano de chegada ao Brasil",
                                  default=None)

    @api.model
    @api.onchange('address_home_id')
    def onchange_address_home_id(self):
        if self.address_home_id:
            if self.address_home_id.cnpj_cpf:
                self.check_cpf = True
                self.cpf = self.address_home_id.cnpj_cpf
            else:
                self.check_cpf = False
                self.cpf = False

    @api.multi
    def onchange_user(self, user_id):
        res = super(HrEmployee, self).onchange_user(user_id)
        partner = self.env['res.partner'].search(
            [('user_ids', '=', user_id)], limit=1)
        res['value'].update({'address_home_id': partner.id})
        return res


class HrEmployeeDependent(models.Model):
    _name = 'hr.employee.dependent'
    _description = 'Employee\'s Dependents'

    employee_id = fields.Many2one(comodel_name='hr.employee',
                                  string=u'Funcionário')
    dependent_name = fields.Char(string=u'Nome', size=64, required=True)
    dependent_dob = fields.Date(string=u'Data de Nascimento', required=True)
    dependent_type_id = fields.Many2one(string='Grau de parentesco',
                                        required=True,
                                        comodel_name='hr.dependent.type')
    pension_benefits = fields.Float(string=u'Valor da Pensão')
    dependent_verification = fields.Boolean(string=u'É dependente')
    health_verification = fields.Boolean(string=u'Utiliza o plano de saúde')
    dependent_gender = fields.Selection(string='Sexo', selection=[
        ('m', 'Masculino'),
        ('f', 'Feminino')])
    dependent_rg = fields.Char(string='RG')
    dependent_cpf = fields.Char(string='CPF')

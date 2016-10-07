# -*- coding: utf-8 -*-
# (c) 2014 Kmee - Rafael da Silva Lima <rafael.lima@kmee.com.br>
# (c) 2014 Kmee - Matheus Felix <matheus.felix@kmee.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import models, fields, api
from datetime import datetime
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
import openerp.addons.decimal_precision as dp
from openerp.exceptions import Warning as UserError


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

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
                    raise UserError(u'PIS/PASEP inválido')
                continue
            if c.isdigit():
                digits.append(int(c))
                continue
            raise UserError(u'PIS/PASEP inválido')
        if len(digits) != 11:
            raise UserError(u'PIS/PASEP inválido')
        height = [int(x) for x in "3298765432"]
        total = 0
        for i in range(10):
            total += digits[i] * height[i]
        rest = total % 11
        if rest != 0:
            rest = 11 - rest
        if not rest == digits[10]:
            raise UserError(u'PIS/PASEP inválido')

    check_cpf = fields.Boolean('Verificar CPF', default=True)
    pis_pasep = fields.Char(u'PIS/PASEP', size=15)
    ctps = fields.Char('CTPS', help=u'Número do CTPS')
    ctps_series = fields.Char('Série')
    ctps_date = fields.Date(u'Data de emissão')
    creservist = fields.Char('Título de reservista')
    cresv_categ = fields.Char('Categoria de reservista')
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

    @api.constrains('dependent_dob')
    def _check_birth(self):
        if datetime.strptime(self.dependent_dob, DEFAULT_SERVER_DATE_FORMAT
                             ).date() > datetime.now().date():
            raise UserError('Data de nascimento do dependente inválida')

    employee_id = fields.Many2one(comodel_name='hr.employee',
                                  string=u'Funcionário')
    dependent_name = fields.Char(string=u'Nome', size=64, required=True)
    dependent_dob = fields.Date(string=u'Data de Nascimento', required=True)
    dependent_type = fields.Char(string=u'Relação', required=True)
    pension_benefits = fields.Float(string=u'Valor da Pensão')
    dependent_verification = fields.Boolean(string=u'É dependente')
    health_verification = fields.Boolean(string=u'Utiliza o plano de saúde')

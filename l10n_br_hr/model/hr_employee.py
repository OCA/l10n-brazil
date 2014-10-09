<<<<<<< HEAD
# -*- coding: utf-8 -*-
# (c) 2014 Kmee - Rafael da Silva Lima <rafael.lima@kmee.com.br>
# (c) 2014 Kmee - Matheus Felix <matheus.felix@kmee.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import models, fields, api
from datetime import datetime
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
from openerp.exceptions import Warning as UserError


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    @api.constrains('pis_pasep')
    def _validate_pis_pasep(self):
        employee = self
        if not employee.pis_pasep:
            return True
=======
# -*- encoding: utf-8 -*-
##############################################################################
#
#    Brazillian Human Resources Payroll module for OpenERP
#    Copyright (C) 2014 KMEE (http://www.kmee.com.br)
#    @author Rafael da Silva Lima <rafael.lima@kmee.com.br>
#            Matheus Felix <matheus.felix@kmee.com.br>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from osv import fields,osv
from datetime import datetime
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
import openerp.addons.decimal_precision as dp


class HrEmployee(osv.osv):   
    
    def _get_dependents(self, cr, uid, ids, fields, arg, context=None):   
        res = {}
        dependent = self.pool.get('hr.employee.dependent')
        dep_ids =  dependent.search(cr, uid, [('employee_id', '=', ids[0]),('dependent_verification','=',True)])
        if dep_ids:
            res[ids[0]] = len(dep_ids)*179.71
            return res
        else:
            res[ids[0]] = 0
            return res
                
    def _validate_pis_pasep(self, cr, uid, ids):
        employee = self.browse(cr, uid, ids[0])

        if not employee.pis_pasep:
            return True

>>>>>>> [NEW] Modulo de localicazão dos recursos humanos
        digits = []
        for c in employee.pis_pasep:
            if c == '.' or c == ' ' or c == '\t':
                continue
<<<<<<< HEAD
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
=======

            if c == '-':
                if len(digits) != 10:
                    return False
                continue

            if c.isdigit():
                digits.append(int(c))
                continue

            return False
        if len(digits) != 11:
            return False

        height = [int(x) for x in "3298765432"]

        total = 0

        for i in range(10):
            total += digits[i] * height[i]

        rest = total % 11
        if rest != 0:
            rest = 11 - rest
        return (rest == digits[10])
    
    _inherit='hr.employee'

    _columns = {
        'check_cpf': fields.boolean('Check CPF'),
        'pis_pasep': fields.char(u'PIS/PASEP', size=15),
        'ctps' : fields.char('CTPS', help='Number of CTPS'), 
        'ctps_series' : fields.char('Serie'),
        'ctps_date' : fields.date('Date of issue'),
        'creservist': fields.char('Certificate of Reservist'),
        'crresv_categ': fields.char('Category'),
        'cr_categ': fields.selection([('estagiario', 'Trainee'), ('junior', 'Junior'),
                                        ('pleno', 'Full'), ('sênior', 'Senior')], 'Category'
                                    , help="Choose work position"),
        'ginstru': fields.selection([
                    ('fundamental_incompleto', 'Basic Education incomplete'), 
                    ('fundamental', 'Basic Education complete'),
                    ('medio_incompleto', 'High School incomplete'),
                    ('medio', 'High School complete'),
                    ('superior_incompleto', 'College Degree incomplete'),
                    ('superior', 'College Degree complete'),
                    ('mestrado', 'Master'),
                    ('doutorado', 'PhD')], 'Schooling',
                                help="Select Education"),
        
        'have_dependent': fields.boolean("Associated"),
        'dependent_ids': fields.one2many('hr.employee.dependent', 'employee_id', 'Employee'),
        'rg': fields.char('RG', help='Number of RG'),
        'cpf': fields.related('address_home_id', 'cnpj_cpf', type='char', string='CPF', required=True),
        'organ_exp': fields.char("Organ Shipping"),
        'rg_emission': fields.date('Date of issue'),
        'title_voter': fields.char('Title', help='Number Voter'),
        'zone_voter': fields.char('Zone'),
        'session_voter': fields.char('Section'),
        'driver_license': fields.char('Driver License', help='Driver License number'),
        'driver_categ':fields.char('Category'),
        'father_name': fields.char('Father name'),
        'mother_name': fields.char('Mother name'),
        'validade': fields.date('Expiration'),
        'sindicate': fields.char('Sindicato', help="Sigla do Sindicato"),
        'n_dependent': fields.function(_get_dependents, type="float", digits_compute=dp.get_precision('Payroll')),

    }    

    _constraints = [[_validate_pis_pasep, u'PIS/PASEP is invalid.', ['pis_pasep']]]

    _defaults = {
        'check_cpf': True
    }

    def onchange_address_home_id(self, cr, uid, ids, address, context=None):
        if address:
            address = self.pool.get('res.partner').browse(cr, uid, address, context=context)

            if address.cnpj_cpf:
                return {'value': {'check_cpf': True, 'cpf': address.cnpj_cpf}}
            else:
                return {'value': {'check_cpf': False, 'cpf': False}}
        return {'value': {}}

    def onchange_no_cpf(self, cr, uid, ids, no_cpf, address_home_id, context=None):
        if no_cpf:

            partner = self.pool.get('res.partner').browse(cr, uid, address_home_id)


    def onchange_user(self, cr, uid, ids, user_id, context=None):

        res = super(HrEmployee, self).onchange_user(cr, uid, ids, user_id, context)

        obj_partner = self.pool.get('res.partner')
        partner_id = obj_partner.search(cr, uid, [('user_ids', '=', user_id)])[0]
        partner = obj_partner.browse(cr, uid, partner_id)

        res['value'].update({'address_home_id': partner.id, 'cpf': partner.cnpj_cpf})
        return res

class HrEmployeeDependent(osv.osv):
    _name = 'hr.employee.dependent'
    _description='Employee\'s Dependents'
    
    def _check_birth(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0], context=context)
        if datetime.strptime(obj.dependent_age, DEFAULT_SERVER_DATE_FORMAT).date() > datetime.now().date():
            return False
        return True
    
     
    _columns = {
        'employee_id' : fields.many2one('hr.employee', 'Employee'),
        'dependent_name' : fields.char('Name', size=64, required=True, translate=True),
        'dependent_age' : fields.date('Date of Birth', required=True),
        'dependent_type': fields.char('Type Associate', required=True),
        'pension_benefits': fields.float('Child Support'),
        'dependent_verification': fields.boolean('Is dependent', required=False),
        'health_verification': fields.boolean('Health Plan', required=False),
       }
    
    _constraints = [[_check_birth, u'Wrong birthday date!', ['dependent_age']]] 
    
>>>>>>> [NEW] Modulo de localicazão dos recursos humanos

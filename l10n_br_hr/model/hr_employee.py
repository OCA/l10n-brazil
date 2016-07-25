# -*- coding: utf-8 -*-
# (c) 2014 Kmee - Rafael da Silva Lima <rafael.lima@kmee.com.br>
# (c) 2014 Kmee - Matheus Felix <matheus.felix@kmee.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp.osv import orm, fields
from datetime import datetime
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
import openerp.addons.decimal_precision as dp


class HrEmployee(orm.Model):
    
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

        digits = []
        for c in employee.pis_pasep:
            if c == '.' or c == ' ' or c == '\t':
                continue

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

class HrEmployeeDependent(orm.Model):
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
    

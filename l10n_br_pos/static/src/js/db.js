/******************************************************************************
*    Point Of Sale - L10n Brazil Localization for POS Odoo
*    Copyright (C) 2016 KMEE INFORMATICA LTDA (http://www.kmee.com.br)
*    @author Luis Felipe Miléo <mileo@kmee.com.br>
*
*    This program is free software: you can redistribute it and/or modify
*    it under the terms of the GNU Affero General Public License as
*    published by the Free Software Foundation, either version 3 of the
*    License, or (at your option) any later version.
*    This program is distributed in the hope that it will be useful,
*    but WITHOUT ANY WARRANTY; without even the implied warranty of
*    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
*    GNU Affero General Public License for more details.
*    You should have received a copy of the GNU Affero General Public License
*    along with this program.  If not, see <http://www.gnu.org/licenses/>.
*
******************************************************************************/

function l10n_br_pos_db(instance, module) {

    module.PosDB = module.PosDB.extend({
        init: function (options) {
            options = options || {};
            this._super(options);
        },
        _partner_search_string: function(partner){
            // FIXME: Call super
            //var str = this._super(partner);
            var str =  partner.name;
            if(partner.ean13){
                str += '|' + partner.ean13;
            }
            if(partner.address){
                str += '|' + partner.address;
            }
            if(partner.phone){
                str += '|' + partner.phone.split(' ').join('');
            }
            if(partner.mobile){
                str += '|' + partner.mobile.split(' ').join('');
            }
            if(partner.email){
                str += '|' + partner.email;
            }
            if(partner.cnpj_cpf){
                var cnpj_cpf =  partner.cnpj_cpf
                str += '|' + cnpj_cpf;
                cnpj_cpf = cnpj_cpf.replace(
                    '.','').replace('/','').replace('-','')
                str += '|' + cnpj_cpf;
            }
            str = '' + partner.id + ':' + str.replace(':','') + '\n';
            return str;
        }
    })
}




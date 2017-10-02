/******************************************************************************
*    Point Of Sale - L10n Brazil Localization for POS Odoo
*    Copyright (C) 2016 KMEE INFORMATICA LTDA (http://www.kmee.com.br)
*    @author Luis Felipe Miléo <mileo@kmee.com.br>
*    @author Luiz Felipe do Divino <luiz.divino@kmee.com.br>
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
        },
        get_partner_by_identification: function(partners, identification){
            var identification_with_pontuation = this.add_pontuation_document(identification);
            for (var i = 0; i < partners.length; i++){
                var cnpj_cpf = partners[i].cnpj_cpf;
                if (cnpj_cpf){
                    if ((cnpj_cpf == identification) || (cnpj_cpf == identification_with_pontuation)){
                        return partners[i];
                    }
                }
            }
            return false;
        },
        add_pontuation_document: function(document){
            var document_with_pontuation = '';
            if(document.length <= 11){
                for (var j = 1; j <= document.length; j++){
                    if ((j == 3) || (j == 6)){
                        document_with_pontuation += document.split('')[j-1] + ".";
                    }else if (j == 9){
                        document_with_pontuation += document.split('')[j-1] + "-";
                    }else{
                        document_with_pontuation += document.split('')[j-1];
                    }
                }
            }else if(document.length > 11 && document.length <= 14){
                for (var j = 1; j <= document.length; j++){
                    if ((j == 2) || (j == 5)){
                        document_with_pontuation += document.split('')[j-1] + ".";
                    }else if (j == 8){
                        document_with_pontuation += document.split('')[j-1] + "/";
                    }else if (j == 12){
                        document_with_pontuation += document.split('')[j-1] + "-";
                    }else{
                        document_with_pontuation += document.split('')[j-1];
                    }
                }
            }
            return document_with_pontuation;
        },
        search_partner: function(query){
            try {
                query = query.replace(/[\[\]\(\)\+\*\?\.\-\!\&\^\$\|\~\_\{\}\:\,\\\/]/g,'.');
                query = query.replace(' ','.+');
                var re = RegExp("([0-9]+):.*?"+query,"gi");
            }catch(e){
                return [];
            }
            var results = [];
            for(var i = 0; i < this.limit; i++){
                r = re.exec(this.partner_search_string);
                if(r){
                    var id = Number(r[1]);
                    results.push(this.get_partner_by_id(id));
                }else{
                    break;
                }
            }
            return results;
        }
    })
}




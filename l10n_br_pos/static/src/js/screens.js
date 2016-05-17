/******************************************************************************
*    Point Of Sale - L10n Brazil Localization for POS Odoo
*    Copyright (C) 2016 KMEE INFORMATICA LTDA (http://www.kmee.com.br)
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

function l10n_br_pos_screens(instance, module) {
    var QWeb = instance.web.qweb;
    var _t = instance.web._t;

    module.HaveCpfCnpj = module.OrderWidget.include({
        template: 'PosWidget',

        init: function(parent, options){
            this._super(parent);
            var self = this;
        },
        renderElement: function() {
            var self = this;
            this._super();
//            console.log(self);
            var partner = null;
            this.el.querySelector('.btn-busca-cpf-cnpj').addEventListener('click',this.search_handler);
            $('.btn-busca-cpf-cnpj', this.el).click(function(e){
                if (self.verificar_cpf_cnpj($('.busca-cpf-cnpj').val())){
                    partner = self.pos.db.get_partner_by_identification(self.pos.partners,$('.busca-cpf-cnpj').val());
                    self.old_client = partner;
                    self.new_client = self.old_client;
                    if (partner){
                        self.pos.get('selectedOrder').set_client(self.new_client);
                    }else{
                        self.pos_widget.screen_selector.show_popup('confirm',{
                            message: _t('Usuario nao encontrado!'),
                            comment: _t('Gostaria de cadastrar este CPF/CNPJ?'),
                            confirm: function(){
                                console.log($('.busca-cpf-cnpj').val());
                                new_partner = {};
                                new_partner["name"] = $('.busca-cpf-cnpj').val();
                                if (new_partner["name"].length > 11){
                                    new_partner["is_company"] = true;
                                }
                                new_partner["cnpj_cpf"] = $('.busca-cpf-cnpj').val();
                                new_partner["property_account_receivable"] = 9;
                                new_partner["property_account_payable"] = 17;
    //                            console.log(new_partner);
                                self.save_client_details(new_partner);
                            },
                        });
                    }
                } else {
                    self.pos_widget.screen_selector.show_popup('error',{
                        message: _t('CPF/CNPJ digitado esta incorreto!'),
                    });
                }
            });
        },
        save_client_details: function(partner) {
            var self = this;

            if (!partner.name) {
                this.pos_widget.screen_selector.show_popup('error',{
                    message: _t('A Customer Name Is Required'),
                });
                return;
            }

            new instance.web.Model('res.partner').call('create_from_ui',[partner]).then(function(partner_id){
                self.old_client = partner;
                self.new_client = self.old_client;
                self.pos.get('selectedOrder').set_client(self.new_client);
            },function(err,event){
                event.preventDefault();
                self.pos_widget.screen_selector.show_popup('error',{
                    'message':_t('Error: Could not Save Changes'),
                    'comment':_t('Your Internet connection is probably down.'),
                });
            });
        },
        verificar_cpf_cnpj: function(documento){
            if (documento.length <= 11){
                var Soma;
                var Resto;
                Soma = 0;
                if (documento == "00000000000") return false;

                for (i=1; i<=9; i++) Soma = Soma + parseInt(documento.substring(i-1, i)) * (11 - i);
                Resto = (Soma * 10) % 11;

                if ((Resto == 10) || (Resto == 11))  Resto = 0;
                if (Resto != parseInt(documento.substring(9, 10)) ) return false;

                Soma = 0;
                for (i = 1; i <= 10; i++) Soma = Soma + parseInt(documento.substring(i-1, i)) * (12 - i);
                Resto = (Soma * 10) % 11;

                if ((Resto == 10) || (Resto == 11))  Resto = 0;
                if (Resto != parseInt(documento.substring(10, 11) ) ) return false;
                return true;
            }else{
                documento = documento.replace(/[^\d]+/g,'');

                if(documento == '') return false;

                if (documento.length != 14)
                    return false;

                // Elimina CNPJs invalidos conhecidos
                if (documento == "00000000000000" ||
                    documento == "11111111111111" ||
                    documento == "22222222222222" ||
                    documento == "33333333333333" ||
                    documento == "44444444444444" ||
                    documento == "55555555555555" ||
                    documento == "66666666666666" ||
                    documento == "77777777777777" ||
                    documento == "88888888888888" ||
                    documento == "99999999999999")
                    return false;

                // Valida DVs
                tamanho = documento.length - 2
                numeros = documento.substring(0,tamanho);
                digitos = documento.substring(tamanho);
                soma = 0;
                pos = tamanho - 7;
                for (i = tamanho; i >= 1; i--) {
                  soma += numeros.charAt(tamanho - i) * pos--;
                  if (pos < 2)
                        pos = 9;
                }
                resultado = soma % 11 < 2 ? 0 : 11 - soma % 11;
                if (resultado != digitos.charAt(0))
                    return false;

                tamanho = tamanho + 1;
                numeros = documento.substring(0,tamanho);
                soma = 0;
                pos = tamanho - 7;
                for (i = tamanho; i >= 1; i--) {
                  soma += numeros.charAt(tamanho - i) * pos--;
                  if (pos < 2)
                        pos = 9;
                }
                resultado = soma % 11 < 2 ? 0 : 11 - soma % 11;
                if (resultado != digitos.charAt(1))
                      return false;

                return true;
            }

        }
    })
}
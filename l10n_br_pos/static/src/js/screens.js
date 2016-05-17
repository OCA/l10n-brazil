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
            console.log(self);
            var partner = null;
            this.el.querySelector('.btn-busca-cpf-cnpj').addEventListener('click',this.search_handler);
            $('.btn-busca-cpf-cnpj', this.el).click(function(e){
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

                console.log(partner);
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
        }
    })
}
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

            var partner = null;
            var isSave = null;

            this.el.querySelector('.busca-cpf-cnpj').addEventListener('keydown',this.search_handler);
            $('.busca-cpf-cnpj', this.el).keydown(function(e){
                if(e.which == 13){
                    var documento = $('.busca-cpf-cnpj').val().replace(/[^\d]+/g,'');
                    if (self.verificar_cpf_cnpj(documento)){
                        partner = self.pos.db.get_partner_by_identification(self.pos.partners, documento);
                        self.old_client = partner;
                        self.new_client = self.old_client;
                        if (partner){
                            self.pos.get('selectedOrder').set_client(self.new_client);
                        }else{
                            if (self.pos.config.save_identity_automatic){
                                new_partner = {};
                                new_partner["name"] = documento;
                                if (new_partner["name"].length > 11){
                                    new_partner["is_company"] = true;
                                }
                                new_partner["cnpj_cpf"] = documento;
                                // new_partner["property_account_receivable"] = 9;
                                // new_partner["property_account_payable"] = 17;
                                self.pos_widget.order_widget.save_client_details(new_partner);
                            }
                        }
                    } else {
                        self.pos_widget.screen_selector.show_popup('error',{
                            message: _t('CPF/CNPJ digitado esta incorreto!'),
                        });
                    }
                }
            });

            this.el.querySelector('.btn-busca-cpf-cnpj').addEventListener('click',this.search_handler);
            $('.btn-busca-cpf-cnpj', this.el).click(function(e){
                var documento = $('.busca-cpf-cnpj').val().replace(/[^\d]+/g,'');
                if (self.verificar_cpf_cnpj(documento)){
                    partner = self.pos.db.get_partner_by_identification(self.pos.partners, documento);
                    self.old_client = partner;
                    self.new_client = self.old_client;
                    if (partner){
                        self.pos.get('selectedOrder').set_client(self.new_client);
                    }else{
                        if (self.pos.config.save_identity_automatic){
                            new_partner = {};
                            new_partner["name"] = documento;
                            if (new_partner["name"].length > 11){
                                new_partner["is_company"] = true;
                            }
                            new_partner["cnpj_cpf"] = documento;
                            // new_partner["property_account_receivable"] = 9;
                            // new_partner["property_account_payable"] = 17;
                            self.pos_widget.order_widget.save_client_details(new_partner);
                        }
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

            var fields = {}
            this.$('.client-details-contents .detail').each(function(idx,el){
                fields[el.name] = el.value;
            });

            if (!partner.name) {
                this.pos_widget.screen_selector.show_popup('error',{
                    message: _t('Um nome de usu?rio ? obrigat?rio'),
                });
                return;
            }

            fields.id           = partner.id || false;
            fields.country_id   = fields.country_id || false;
            fields.ean13        = fields.ean13 ? this.pos.barcode_reader.sanitize_ean(fields.ean13) : false;

            new instance.web.Model('res.partner').call('create_from_ui',[partner]).then(function(partner_id){
                self.pos.pos_widget.clientlist_screen.reload_partners().then(function(){
                    var new_partner = self.pos.db.get_partner_by_id(partner_id);
                    new_partner['cnpj_cpf'] = new_partner['name'];
                    if (self.pos.config.pricelist_id){
                       new_partner['property_product_pricelist'][0] = self.pos.pricelist.id;
                    }
                    self.old_client = new_partner;
                    self.new_client = self.old_client;
                    self.pos.get('selectedOrder').set_client(self.new_client);
                    if (self.pos.config.pricelist_id){
                        self.pos.pricelist_engine.update_products_ui(self.new_client);
                    }
                    return true;
                });
            },function(err,event){
                event.preventDefault();
                self.pos_widget.screen_selector.show_popup('error',{
                    'message':_t('Error: N?o foi poss?vel salvar o cpf'),
                    'comment':_t('O cpf j? existe no sistema ou n?o foi poss?vel cadastra-lo no banco de dados.'),
                });
                return false;
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
    });

    module.PaypadWidget = module.PosBaseWidget.extend({
        template: 'PaypadWidget',
        renderElement: function() {
            var self = this;
            this._super();

            var button = new module.PosOrderListButtonWidget(self,{
                pos: self.pos,
                pos_widget : self.pos_widget,
            });
            button.appendTo(self.$el);

            _.each(this.pos.cashregisters,function(cashregister) {
                var button = new module.PaypadButtonWidget(self,{
                    pos: self.pos,
                    pos_widget : self.pos_widget,
                    cashregister: cashregister,
                });
                button.appendTo(self.$el);
            });

        }
    });

    module.PosOrderListButtonWidget = module.PosBaseWidget.extend({
        template: 'PosOrderListButtonWidget',
        init: function(parent, options){
            this._super(parent, options);
            this.cashregister = options.cashregister;
        },
        renderElement: function() {
            var self = this;
            this._super();

            this.$el.click(function(){
                var ss = self.pos.pos_widget.screen_selector;
                if(ss.get_current_screen() === 'posordertlist'){
                    ss.back();
                }else if (ss.get_current_screen() !== 'receipt'){
                    ss.set_current_screen('posordertlist');
                }
            });
        },
    });

    module.PaymentScreenWidget = module.PaymentScreenWidget.extend({
        validate_order: function(options) {
            this._super();
            options = options || {};
            var currentOrder = this.pos.get('selectedOrder');

            // var status = this.pos.proxy.get('status');
            // var sat_status = status.drivers.satcfe ? status.drivers.satcfe.status : false;
            // if( sat_status == 'connected'){
                if(options.invoice){
                    // deactivate the validation button while we try to send the order
                    this.pos_widget.action_bar.set_button_disabled('validation',true);
                    this.pos_widget.action_bar.set_button_disabled('invoice',true);

                    var invoiced = this.pos.push_and_invoice_order(currentOrder);

                    invoiced.fail(function(error){
                        if(error === 'error-no-client'){
                            self.pos_widget.screen_selector.show_popup('error',{
                                message: _t('An anonymous order cannot be invoiced'),
                                comment: _t('Please select a client for this order. This can be done by clicking the order tab'),
                            });
                        }else{
                            self.pos_widget.screen_selector.show_popup('error',{
                                message: _t('The order could not be sent'),
                                comment: _t('Check your internet connection and try again.'),
                            });
                        }
                        self.pos_widget.action_bar.set_button_disabled('validation',false);
                        self.pos_widget.action_bar.set_button_disabled('invoice',false);
                    });

                    invoiced.done(function(){
                        self.pos_widget.action_bar.set_button_disabled('validation',false);
                        self.pos_widget.action_bar.set_button_disabled('invoice',false);
                        self.pos.get('selectedOrder').destroy();
                    });

                }else{
                    var retorno_sat = {};
                    if(this.pos.config.iface_sat_via_proxy){
                        var receipt = currentOrder.export_for_printing();
                        var json = currentOrder.export_for_printing();
                        this.pos.proxy.send_order_sat(
                            currentOrder,
                            QWeb.render('XmlReceipt',{
                            receipt: receipt, widget: self,
                        }), json);
                        this.pos.get('selectedOrder').destroy();
                    }else{
                        this.pos.push_order(currentOrder);
                    }

                    if(this.pos.config.iface_print_via_proxy){
                        var receipt = currentOrder.export_for_printing();
                        this.pos.proxy.print_receipt(
                            QWeb.render('XmlReceipt',{
                            receipt: receipt, widget: self,
                        }));
                        this.pos.get('selectedOrder').destroy();    //finish order and go back to scan screen
                    }else{
                        this.pos_widget.screen_selector.set_current_screen(this.next_screen);
                    }
                }
            // }else{
            //     self.pos_widget.screen_selector.show_popup('error',{
            //         message: _t('SAT n\u00e3o est\u00e1 conectado'),
            //         comment: _t('Verifique se existe algum problema com o SAT e tente fazer a requisi\u00e7\u00e3o novamente.'),
            //     });
            // }
        }
    });

    module.PosOrderListScreenWidget = module.ScreenWidget.extend({
        template: 'PosOrderListScreenWidget',

        init: function(parent, options){
            this._super(parent, options);
            this.orders = {};
            // var self = this;
            // this.get_last_orders();
        },

        show_leftpane: false,

        auto_back: true,

        show: function(){
            var self = this;
            this._super();

            this.renderElement();
            this.details_visible = false;
            this.get_last_orders();

            this.$('.back').click(function(){
                self.pos_widget.screen_selector.back();
            });

            this.render_list(self.orders.Orders);
            this.$('.client-list-contents').delegate('.cancel_order','click',function(event){
                var order_id = $(this).parent().parent().data('id');
                self.pos_widget.screen_selector.show_popup('confirm',{
                            message: _t('Cancelar Venda'),
                            comment: _t('Voc\u00ea realmente deseja cancelar est\u00e1 venda?'),
                            confirm: function(){
                                var posOrderModel = new instance.web.Model('pos.order');
                                var posOrder = posOrderModel.call('retornar_order_by_id', {'order_id': order_id})
                                .then(function (order) {
                                    self.cancel_last_order_sat(order);
                                });
                            },
                        });

            });
            this.$('.client-list-contents').delegate('.reprint_order','click',function(event){
                self.reprint_cfe($(this).parent().parent().data('id'));
            });
        },
        get_last_orders: function(){
            var self = this;

            var session_id = {'session_id': self.pos.pos_session.id};
            var posOrderModel = new instance.web.Model('pos.order');
            var posOrder = posOrderModel.call('return_orders_from_session', session_id)
            .then(function (orders) {
                self.orders = orders;
            });
        },
        reprint_cfe: function(order_id){
            var self = this;

            var posOrderModel = new instance.web.Model('pos.order');
            var posOrder = posOrderModel.call('retornar_order_by_id', {'order_id': order_id})
            .then(function (result) {
                self.pos.proxy.reprint_cfe(result);
            });
        },
        render_list: function(orders){
            var orders_vals = orders;

            var contents = this.$el[0].querySelector('.client-list-contents');
            contents.innerHTML = "";
            for(var i = 0; i < orders_vals.length; i++){
                var order    = orders_vals[i];
                var clientline_html = QWeb.render('OrderLine',{widget: this, order:orders_vals[i]});
                var clientline = document.createElement('tbody');
                clientline.innerHTML = clientline_html;
                clientline = clientline.childNodes[1];

                contents.appendChild(clientline);
            }
        },
        cancel_last_order_sat: function(order){
            var self = this;

            var status = this.pos.proxy.get('status');
            var sat_status = status.drivers.satcfe ? status.drivers.satcfe.status : false;
            if( sat_status == 'connected'){
                if(this.pos.config.iface_sat_via_proxy){
                    this.pos.proxy.cancel_last_order(order);
                }
            }
        },
        close: function(){
            this._super();
        },
    });

    module.ReceiptScreenWidget = module.ReceiptScreenWidget.extend({
        template: 'ReceiptScreenWidget',

        finishOrder: function() {
            this.pos_widget.posorderlist_screen.get_last_orders();
            this.pos.get('selectedOrder').destroy();
        }
    });
}
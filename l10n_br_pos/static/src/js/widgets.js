/******************************************************************************
*    Point Of Sale - L10n Brazil Localization for POS Odoo
*    Copyright (C) 2016 KMEE INFORMATICA LTDA (http://www.kmee.com.br)
*    @author Luis Felipe Mil?o <mileo@kmee.com.br>
*    @author Luiz Felipe do Divino <luiz.divino@kmee.com.br>
*
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
function l10n_br_pos_widgets(instance, module){
    var QWeb = instance.web.qweb;
	var _t = instance.web._t;

    module.ProxyStatusWidget = module.ProxyStatusWidget.extend({
        template: 'ProxyStatusWidget',
    	set_smart_status: function(status){
            if(status.status === 'connected'){
                var warning = false;
                var msg = ''
                if(this.pos.config.iface_scan_via_proxy){
                    var scanner = status.drivers.scanner ? status.drivers.scanner.status : false;
                    if( scanner != 'connected' && scanner != 'connecting'){
                        warning = true;
                        msg += _t('Scanner');
                    }
                }
                if( this.pos.config.iface_print_via_proxy ||
                    this.pos.config.iface_cashdrawer ){
                    var printer = status.drivers.escpos ? status.drivers.escpos.status : false;
                    if( printer != 'connected' && printer != 'connecting'){
                        warning = true;
                        msg = msg ? msg + ' & ' : msg;
                        msg += _t('Printer');
                    }
                }
                if( this.pos.config.iface_electronic_scale ){
                    var scale = status.drivers.scale ? status.drivers.scale.status : false;
                    if( scale != 'connected' && scale != 'connecting' ){
                        warning = true;
                        msg = msg ? msg + ' & ' : msg;
                        msg += _t('Scale');
                    }
                }
                var sat = status.drivers.satcfe ? status.drivers.satcfe.status : false;
                if( sat != 'connected' && sat != 'connecting'){
                    warning = true;
                    msg = msg ? msg + ' & ' : msg;
                    msg += _t('SAT');
                }
                msg = msg ? msg + ' ' + _t('Offline') : msg;
                this.set_status(warning ? 'warning' : 'connected', msg);
            }else{
                this.set_status(status.status,'');
            }
        }
    });

    var PaypadButtonWidget = module.PosBaseWidget;

    module.PaypadButtonWidget = module.PaypadButtonWidget.extend({
        renderElement: function() {
            var self = this;
            PaypadButtonWidget.prototype.renderElement.apply(this);

            this.$el.click(function() {
                if (self.pos.get('selectedOrder').get('orderLines').length == 0){
                    self.pos.pos_widget.screen_selector.show_popup('error',{
                        message: 'Nenhum produto selecionado!',
                        comment: 'Você precisa selecionar pelo menos um produto para abrir a tela de pagamentos',
                    });
                } else {
                    if (self.pos.get('selectedOrder').get('screen') === 'receipt'){  //TODO Why ?
                        console.warn('TODO should not get there...?');
                        return;
                    }
                    self.pos.get('selectedOrder').addPaymentline(self.cashregister);
                    self.pos_widget.screen_selector.set_current_screen('payment');
                }
            });
        }
    });

    module.CPFNaNotaPopupWidgetPrimeiraCompra = module.PopUpWidget.extend({
        template: 'CPFNaNotaPrimeiraCompra',
        hotkeys_handlers: {},

        calcula_diferenca_data: function(data_alteracao){
            var today = new Date();
            var month = parseInt(today.getMonth())+1;
            var year = today.getFullYear();
            var year_partner = parseInt(data_alteracao.substring(0,4));
            var month_partner  = parseInt(data_alteracao.substring(5,7));
            var lim_data_alteracao = parseInt(this.pos.config.lim_data_alteracao);

            if ((year - year_partner) == 0 && (month_partner + lim_data_alteracao) >= month)
                return true;
            else if ((year - year_partner) == 1 && (month_partner + lim_data_alteracao) >= 12+month)
                return true;

            return false;
        },

        search_client_by_cpf_cnpj: function(documento) {
            var self = this;

            if (self.verificar_cpf_cnpj(documento.replace(/[^\d]+/g,''))){
                pos_db = self.pos.db;
                partner = pos_db.get_partner_by_identification(self.pos.partners, documento);
                if(partner){
                    this.active_client(self, documento, partner);
                    if(!this.calcula_diferenca_data(partner.data_alteracao)){
                        var ss = self.pos.pos_widget.screen_selector;
                        ss.set_current_screen('clientlist');
                    }
                } else {
                    documento_pontuacao = pos_db.add_pontuation_document(documento);
                    return new instance.web.Model("res.partner").get_func("search_read")([['cnpj_cpf', '=', documento_pontuacao]], ['name', 'cnpj_cpf', 'country_id']).then(function(res) {
                        if (res){
                            pos_db.add_partners(res);
                        }
                        self.active_client(self, documento, res[0]);
                    },function(err,event) {
                        self.active_client(self, documento, partner);
                    });
                }
            } else {
                self.pos_widget.screen_selector.show_popup('error',{
                    message: _t('CPF/CNPJ digitado esta incorreto!'),
                });
            }
        },

        active_client: function (self, documento, partner) {
            pos_db = self.pos.db;
            self.old_client = partner;
            self.new_client = self.old_client;
            if (partner) {
                self.pos.get('selectedOrder').set_client(self.new_client);
            } else {
                if (self.pos.config.save_identity_automatic) {
                    new_partner = {};
                    new_partner["name"] = pos_db.add_pontuation_document(documento);
                    if (new_partner["name"].length > 14) {
                        new_partner["is_company"] = true;
                    }
                    new_partner["cnpj_cpf"] = pos_db.add_pontuation_document(documento);
                    self.pos_widget.order_widget.save_client_details(new_partner);
                }
            }
        },

        verificar_cpf_cnpj: function(documento){
            if (documento.length <= 11){
                var Soma;
                var Resto;
                Soma = 0;
                if (documento == "00000000000" ||
                    documento == "11111111111" ||
                    documento == "22222222222" ||
                    documento == "33333333333" ||
                    documento == "44444444444" ||
                    documento == "55555555555" ||
                    documento == "66666666666" ||
                    documento == "77777777777" ||
                    documento == "88888888888" ||
                    documento == "99999999999")
                    return false;

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

        },

        ativar_cliente: function(currentOrder){
            self = this;
            var cpf = $('.busca-cpf-cnpj-popup').val();
            if (cpf){
                self.pos_widget.screen_selector.close_popup();
                self.search_client_by_cpf_cnpj(cpf);
            } else {
                alert('O cpf deve ser inserido no campo para que seja transmitido no cupom fiscal.');
            }
        },

        calcula_diferenca_data: function(data_alteracao){
            if(data_alteracao){
                var today = new Date();
                var month = parseInt(today.getMonth())+1;
                var year = today.getFullYear();
                var year_partner = parseInt(data_alteracao.substring(0,4));
                var month_partner  = parseInt(data_alteracao.substring(5,7));
                var lim_data_alteracao = parseInt(this.pos.config.lim_data_alteracao);

                if ((year - year_partner) == 0 && (month_partner + lim_data_alteracao) >= month)
                    return true;
                else if ((year - year_partner) == 1 && (month_partner + lim_data_alteracao) >= 12+month)
                    return true;
            }
            return false;
        },

        show: function(options){
            var self = this;
            this._super();

            this.message = options.message || '';
            this.comment = options.comment || '';
            var cliente_cpf = '';
            var cliente_create_date = '';
            var cliente_atualizados = false;
            var currentOrder = this.pos.get('selectedOrder').attributes;
            if (currentOrder.client) {
                cliente_cpf = currentOrder.client.cnpj_cpf;
                cliente_create_date = currentOrder.client.create_date.substring(0,7);
                cliente_atualizados = currentOrder.client.data_alteracao;
                if (cliente_atualizados == false)
                    cliente_atualizados = cliente_create_date;
            }
            this.cpf_nota = cliente_cpf;
            this.create_date = cliente_create_date;
            this.atualizacao = this.calcula_diferenca_data(cliente_atualizados);

            this.renderElement();

            this.hotkey_handler = function (event) {
                if (event.which === 13) {
                    self.ativar_cliente(currentOrder);
                }
            };

            $('.busca-cpf-cnpj-popup').on('keyup',this.hotkey_handler);

            this.$('.button.sim').click(function(){
                self.ativar_cliente(currentOrder);
            });

            this.$('.button.nao').click(function(){
                self.pos_widget.screen_selector.close_popup();
            });
        }
    });

    module.OrderWidget = module.PosBaseWidget.extend({
        template:'OrderWidget',
        init: function(parent, options) {
            var self = this;
            this._super(parent,options);
            this.editable = false;
            this.pos.bind('change:selectedOrder', this.change_selected_order, this);
            this.line_click_handler = function(event){
                if(!self.editable){
                    return;
                }
                self.pos.get('selectedOrder').selectLine(this.orderline);
                self.pos_widget.numpad.state.reset();
            };
            this.client_change_handler = function(event){
                self.update_summary();
            }
            this.bind_order_events();
        },
        enable_numpad: function(){
            this.disable_numpad();  //ensure we don't register the callbacks twice
            this.numpad_state = this.pos_widget.numpad.state;
            if(this.numpad_state){
                this.numpad_state.reset();
                this.numpad_state.bind('set_value',   this.set_value, this);
            }

        },
        disable_numpad: function(){
            if(this.numpad_state){
                this.numpad_state.unbind('set_value',  this.set_value);
                this.numpad_state.reset();
            }
        },
        set_editable: function(editable){
            this.editable = editable;
            if(editable){
                this.enable_numpad();
            }else{
                this.disable_numpad();
                this.pos.get('selectedOrder').deselectLine();
            }
        },
        set_value: function(val) {
        	var order = this.pos.get('selectedOrder');
        	if (this.editable && order.getSelectedLine()) {
                var mode = this.numpad_state.get('mode');
                if( mode === 'quantity'){
                    order.getSelectedLine().set_quantity(val);
                }else if( mode === 'discount'){
                    order.getSelectedLine().set_discount(val);
                }else if( mode === 'price'){
                    order.getSelectedLine().set_unit_price(val);
                }
        	}
        },
        change_selected_order: function() {
            this.bind_order_events();
            this.renderElement();
        },
        bind_order_events: function() {

            var order = this.pos.get('selectedOrder');
                order.unbind('change:client', this.client_change_handler);
                order.bind('change:client', this.client_change_handler);

            var lines = order.get('orderLines');
                lines.unbind();
                lines.bind('add', function(){
                        this.numpad_state.reset();
                        this.renderElement(true);
                    },this);
                lines.bind('remove', function(line){
                        this.remove_orderline(line);
                        this.numpad_state.reset();
                        this.update_summary();
                    },this);
                lines.bind('change', function(line){
                        this.rerender_orderline(line);
                        this.update_summary();
                    },this);
        },
        render_orderline: function(orderline){
            var el_str  = openerp.qweb.render('Orderline',{widget:this, line:orderline});
            var el_node = document.createElement('div');
                el_node.innerHTML = _.str.trim(el_str);
                el_node = el_node.childNodes[0];
                el_node.orderline = orderline;
                el_node.addEventListener('click',this.line_click_handler);

            orderline.node = el_node;
            return el_node;
        },
        remove_orderline: function(order_line){
            if(this.pos.get('selectedOrder').get('orderLines').length === 0){
                this.renderElement();
            }else{
                order_line.node.parentNode.removeChild(order_line.node);
            }
        },
        rerender_orderline: function(order_line){
            var node = order_line.node;
            var replacement_line = this.render_orderline(order_line);
            node.parentNode.replaceChild(replacement_line,node);
        },
        // overriding the openerp framework replace method for performance reasons
        replace: function($target){
            this.renderElement();
            var target = $target[0];
            target.parentNode.replaceChild(this.el,target);
        },
        renderElement: function(scrollbottom){
            this.pos_widget.numpad.state.reset();

            var order  = this.pos.get('selectedOrder');
            var orderlines = order.get('orderLines').models;

            var el_str  = openerp.qweb.render('OrderWidget',{widget:this, order:order, orderlines:orderlines});

            var el_node = document.createElement('div');
                el_node.innerHTML = _.str.trim(el_str);
                el_node = el_node.childNodes[0];


            var list_container = el_node.querySelector('.orderlines');

            if(orderlines.length == 1 && this.pos.config.crm_ativo){
                self.pos_widget.screen_selector.show_popup('cpf_nota_sat_primeira_compra_popup',{
                    message: _t('Deseja inserir o cpf no cupom fiscal?'),
                });
            }

            for(var i = 0, len = orderlines.length; i < len; i++){
                var orderline = this.render_orderline(orderlines[i]);
                list_container.appendChild(orderline);
            }

            if(this.el && this.el.parentNode){
                this.el.parentNode.replaceChild(el_node,this.el);
            }
            this.el = el_node;
            this.update_summary();

            if(scrollbottom){
                this.el.querySelector('.order-scroller').scrollTop = 100 * orderlines.length;
            }
        },
        update_summary: function(){
            var order = this.pos.get('selectedOrder');
            var total     = order ? order.getTotalTaxIncluded() : 0;
            var taxes     = order ? total - order.getTotalTaxExcluded() : 0;

            this.el.querySelector('.summary .total > .value').textContent = this.format_currency(total);
            this.el.querySelector('.summary .total .subentry .value').textContent = this.format_currency(taxes);

        },
    });

    module.PosWidget = module.PosWidget.extend({
        build_widgets: function(){
            this._super();
            var self = this;

            this.cpf_nota_sat_primeira_compra = new module.CPFNaNotaPopupWidgetPrimeiraCompra(this,{});
            this.cpf_nota_sat_primeira_compra.appendTo(this.$('.screens'));
            this.cpf_nota_sat_primeira_compra.hide();
            this.screen_selector.popup_set['cpf_nota_sat_primeira_compra_popup'] = this.cpf_nota_sat_primeira_compra;

            this.cpf_nota_sat = new module.CPFNaNotaPopupWidget(this,{});
            this.cpf_nota_sat.appendTo(this.$('.screens'));
            this.cpf_nota_sat.hide();
            this.screen_selector.popup_set['cpf_nota_sat_popup'] = this.cpf_nota_sat;

            this.last_orders = new module.PosOrderListWidget(this, {});
            this.last_orders.replace(this.$('.placeholder-PosOrderListWidget'));

            this.posorderlist_screen = new module.PosOrderListScreenWidget(this, {});
            this.posorderlist_screen.appendTo(this.$('.screens'));
            this.posorderlist_screen.hide();
            this.screen_selector.screen_set['posordertlist'] = this.posorderlist_screen;
        },
    });

    module.ProductCategoriesWidget = module.ProductCategoriesWidget.extend({
        buscar_produto_backend: function(ean13_produto){
            var self = this;
            produtc_fields = ['categ_id', 'default_code', 'description', 'description_sale', 'display_name', 'ean13', 'estd_national_taxes_perct', 'fiscal_classification_id', 'id', 'list_price', 'mes_type', 'name', 'origin', 'pos_categ_id', 'price', 'price_extra', 'price_with_taxes', 'product_tmpl_id', 'seller_ids', 'standard_price', 'taxes_id', 'to_weight', 'uom_id', 'uos_coeff', 'uos_id'];
            return new instance.web.Model("product.product").get_func("search_read")([['ean13', '=', ean13_produto]], produtc_fields).then(function(res) {
                if (res.length > 0){
                    self.pos.db.add_products(res);
                    self.perform_search(self.category, ean13_produto, false);
                } else {
                    self.pos_widget.screen_selector.show_popup('error',{
                        'message':_t('Erro!'),
                        'comment':_t('Produto não existe no sistema!')
                    });
                }
            },function(err, event){
                event.preventDefault();
                self.pos_widget.screen_selector.show_popup('error',{
                    'message':_t('Erro: Não foi possível acessar o backend!'),
                    'comment':_t('Tente novamente em alguns instantes.')
                });
            });
        },
        renderElement: function() {
            var self = this;
            this._super();
            $('.buscar-produto-backend', this.el).click(function(e){
                self.buscar_produto_backend($('.rightpane-header > .searchbox > input').val());
            });
        }
    });
}
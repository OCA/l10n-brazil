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

    module.PosWidget = module.PosWidget.extend({
        build_widgets: function(){
            this._super();
            var self = this;

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
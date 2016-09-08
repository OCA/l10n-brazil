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

    module.PosWidget = module.PosWidget.extend({
        build_widgets: function(){
            this._super();
            var self = this;

            this.last_orders = new module.PosOrderListWidget(this, {});
            this.last_orders.replace(this.$('.placeholder-PosOrderListWidget'));

            this.posorderlist_screen = new module.PosOrderListScreenWidget(this, {});
            this.posorderlist_screen.appendTo(this.$('.screens'));
            this.posorderlist_screen.hide();
            this.screen_selector.screen_set['posordertlist'] = this.posorderlist_screen;
        },
    });

}
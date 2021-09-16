/*
Copyright (C) 2021-Today KMEE (https://kmee.com.br)
@author: Luis Felipe Mileo <mileo@kmee.com.br>
 License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
*/

odoo.define('l10n_br_pos.chrome', function (require) {
    "use strict";

    var chrome = require('point_of_sale.chrome');

    var core = require('web.core');
    var _t = core._t;

    chrome.ProxyStatusWidget.include({

        set_smart_status: function(status){
            this._super(status);
            if(status.status === 'connected'){
                var warning = this.$('.js_warning.oe_hidden').length == 0;
                var msg = this.$('.js_msg').html();
                if(this.pos.config.iface_fiscal_via_proxy){
                    var display = status.drivers.hw_fiscal ? status.drivers.hw_fiscal.status : false;
                    if( display != 'connected' && display != 'connecting'){
                        warning = true;
                        if (msg){
                            msg = _t('Fiscal') + ' & ' + msg;
                        } else {
                            msg = _t('Fiscal') + ' ' + _t('Offline');
                        }
                    }
                    this.set_status(warning ? 'warning' : 'connected', msg);
                }
            }
        },
    });
});

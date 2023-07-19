/*
Copyright (C) 2016-Today KMEE (https://kmee.com.br)
@author: Luis Felipe Mileo <mileo@kmee.com.br>
@author: Luiz Felipe do Divino <luiz.divino@kmee.com.br>
 License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
*/

odoo.define("l10n_br_pos_cfe.devices", function (require) {
    "use strict";
    var devices = require("point_of_sale.devices");
    var FiscalDocumentCFe = require("l10n_br_pos_cfe.FiscalDocumentCFe")
        .FiscalDocumentCFe;

    var ProxyDeviceSuper = devices.ProxyDevice;

    devices.ProxyDevice = devices.ProxyDevice.extend({
        init: function () {
            var res = ProxyDeviceSuper.prototype.init.apply(this, arguments);
            var self = this;

            this.on("change:status", this, function (eh, status) {
                var new_status = status.newValue;
                if (new_status.status === "connected" && self.fiscal_device) {
                    self.fiscal_device.send_order();
                    // TODO: Criar uma abstração na fila para processar todas as ações.
                }
            });

            return res;
        },
        set_connection_status: function (status) {
            ProxyDeviceSuper.prototype.set_connection_status.apply(this, arguments);
            if (status === "connected" && this.fiscal_device) {
                var oldstatus = this.get("status");
                if (oldstatus.drivers) {
                    if (!oldstatus.drivers.hw_fiscal) {
                        this.fiscal_device.init_job();
                    }
                }
            }
        },
        connect: function () {
            var result = ProxyDeviceSuper.prototype.connect.apply(this, arguments);
            this.connect_to_fiscal_device();
            return result;
        },
        autoconnect: function () {
            var result = ProxyDeviceSuper.prototype.autoconnect.apply(this, arguments);
            this.connect_to_fiscal_device();
            return result;
        },
        keepalive: function () {
            var result = ProxyDeviceSuper.prototype.keepalive.apply(this, arguments);
            return result;
        },
        connect_to_fiscal_device: function () {
            if (this.pos.config.iface_fiscal_via_proxy) {
                this.fiscal_device = new FiscalDocumentCFe(this.host, this.pos);
                this.fiscal_device_contingency = this.fiscal_device;
            }
        },
    });
});

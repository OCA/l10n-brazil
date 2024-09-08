/*
Copyright (C) 2021-Today KMEE (https://kmee.com.br)
@author: Luis Felipe Mileo <mileo@kmee.com.br>
 License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
*/

odoo.define("l10n_br_pos_cfe.ProxyStatus", function (require) {
    "use strict";
    var Registries = require("point_of_sale.Registries");
    var ProxyStatus = require("point_of_sale.ProxyStatus");

    const CustomCFeProxyStatus = (ProxyStatus_status = ProxyStatus) =>
        class CFeProxyStatus extends ProxyStatus_status {
            _setStatus(newStatus) {
                super._setStatus(newStatus);
                var warning = false;
                var msg = "";
                if (this.env.pos.config.iface_fiscal_via_proxy) {
                    var cfeStatus = newStatus.drivers.hw_fiscal
                        ? newStatus.drivers.hw_fiscal.status
                        : false;
                    if (cfeStatus !== "connected" && cfeStatus !== "connecting") {
                        if (msg) {
                            msg = this.env._t("Fiscal") + " & " + msg;
                        } else {
                            msg = this.env._t("Fiscal") + " " + this.env._t("Offline");
                        }
                    }
                    this.state.status = warning ? "warning" : "connected";
                    this.state.msg = msg;
                }
            }
        };
    Registries.Component.extend(ProxyStatus, CustomCFeProxyStatus);
});

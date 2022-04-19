/*
    l10n_br_tef
    Copyright (C) 2018 KMEE INFORMATICA LTDA (http://www.kmee.com.br)
    @author Atilla Graciano da Silva <atilla.silva@kmee.com.br>
    @author Bianca da Rocha Bartolomei <bianca.bartolomei@kmee.com.br>
    @author Hugo Uchôas Borges <hugo.borges@kmee.com.br>
    @author Luis Felipe Mileo  <mileo@kmee.com.br>
    License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
*/

odoo.define('l10n_br_tef.models', function (require) {
    "use strict";

    var models = require('point_of_sale.models');
    var _orderproto = models.Order.prototype;
    var PosModelSuper = models.PosModel;
    var devices = require('point_of_sale.devices');

    var tef_device = require('l10n_br_tef.devices');

    let _super_payment_line = models.Paymentline.prototype;

    models.load_fields('account.journal', ['tef_payment_mode']);

    models.Order = models.Order.extend({
        initialize: function () {
            _orderproto.initialize.apply(this, arguments);
            this.tef_in_transaction = false;
        },
    });

    models.PosModel = models.PosModel.extend({
        initialize: function (session, attributes) {
            var res = PosModelSuper.prototype.initialize.call(this, session, attributes);
            this.tef_client = new tef_device.TefProxy({'pos': this});
            this.tef_queue = new devices.JobQueue();
            this.set({'tef_status': {state: 'disconnected', pending: 0}});
            return res;
        },
    });


    models.Paymentline = models.Paymentline.extend({
        initialize: function (attr, options) {
            _super_payment_line.initialize.call(this, attr, options);

            // Checks if it is a payment method and a debit or credit to be handled by the TEF
            if (this.cashregister.journal.tef_payment_mode) {
                this.tef_payment_completed = this.tef_payment_completed || false;
            } else {
                this.tef_payment_completed = true;
            }
        },
        init_from_JSON: function (json) {
            _super_payment_line.init_from_JSON.apply(this, arguments);
            this.tef_payment_completed = json.tef_payment_completed;
        },
        export_as_JSON: function () {
            const json = _super_payment_line.export_as_JSON.call(this);
            json.tef_payment_completed = this.tef_payment_completed;
            return json;
        },
    });

});

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

    // models.load_fields('account.journal', ['novos_campos']);
    // TODO: Colocar campos no account.journal que diferenciem os modos de pagamento, só ó codigo fica muito solto.

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

});

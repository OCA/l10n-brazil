/******************************************************************************
 *    L10N_BR_TEF
 *    Copyright (C) 2018 KMEE INFORMATICA LTDA (http://www.kmee.com.br)
 *    @author Luis Felipe Miléo <mileo@kmee.com.br>
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

openerp.l10n_br_tef= function(instance){
    module = instance.point_of_sale;

    module.ProxyDevice = module.ProxyDevice.extend({
        tef_transaction_start: function(line, currency_iso){
            var data = {'amount' : line.get_amount(),
                        'currency_iso' : currency_iso,
                        'payment_mode' : line.cashregister.journal.payment_mode};
            this.message('tef_transaction_start', {'payment_info' : JSON.stringify(data)});
        },
    });

    module.PaymentScreenWidget.include({
        render_paymentline: function(line){
            el_node = this._super(line);
            var self = this;

            if (line.cashregister.journal.payment_mode && this.pos.config.iface_tef){

                el_node.querySelector('.payment-terminal-transaction-start')
                    .addEventListener('click', function(){self.pos.proxy.tef_transaction_start(line, self.pos.currency.name)});
                }
            return el_node;
        },
    });

};


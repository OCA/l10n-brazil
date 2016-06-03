/******************************************************************************
*    Point Of Sale - L10n Brazil Localization for POS Odoo
*    Copyright (C) 2016 KMEE INFORMATICA LTDA (http://www.kmee.com.br)
*    @author Luis Felipe Mil?o <mileo@kmee.com.br>
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
function l10n_br_pos_devices(instance, module) {

    module.ProxyDevice = module.ProxyDevice.extend({
        print_receipt: function(receipt, json){
            var self = this;
            if(receipt){
                this.receipt_queue.push(receipt);
                this.receipt_queue.push(json);
            }
            var aborted = false;
            function send_printing_job(){
                if (self.receipt_queue.length > 0){
                    var r = self.receipt_queue.shift();
                    var j = self.receipt_queue.shift();
                    console.log("Segundo json");
                    console.log(self);
                    self.message('print_json_sat',{ receipt: r, json: j },{ timeout: 5000 })
                        .then(function(){
                            send_printing_job();
                        },function(error){
                            if (error) {
                                self.pos.pos_widget.screen_selector.show_popup('error-traceback',{
                                    'message': _t('Printing Error: ') + error.data.message,
                                    'comment': error.data.debug,
                                });
                                return;
                            }
                            self.receipt_queue.unshift(r)
                            self.receipt_queue.unshift(j)
                        });
                }
            }
            send_printing_job();
        }
    });

}
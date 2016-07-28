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
function l10n_br_pos_devices(instance, module) {
    var QWeb = instance.web.qweb;
    var _t = instance.web._t;

    module.ProxyDevice = module.ProxyDevice.extend({
        init_sat: function(config){
            var self = this;
            var j = {
                'sat_path': config.sat_path,
                'codigo_ativacao': config.cod_ativacao,
                'impressora': config.impressora,
                'printer_params': config.printer_params,
                'assinatura': config.assinatura_sat,
            };
            self.message('init',{json: j},{ timeout: 5000 })
        },
        send_order_sat: function(currentOrder, receipt, json){
            var self = this;
            if(receipt){
                this.receipt_queue.push(receipt);
                this.receipt_queue.push(json);
            }
            var aborted = false;
            function send_sat_job(){
                if (self.receipt_queue.length > 0){
                   var r = self.receipt_queue.shift();
                   var j = self.receipt_queue.shift();
                   self.message('enviar_cfe_sat',{json: j},{ timeout: 5000 })
                        .then(function(result){
                            if (!result['excessao']){
                                currentOrder.set_return_cfe(result['xml']);
                                currentOrder.set_num_sessao_sat(result['numSessao']);
                                currentOrder.set_chave_cfe(result['chave_cfe']);
                                self.pos.push_order(currentOrder);
                            }else{
                                self.pos.pos_widget.screen_selector.show_popup('error-traceback',{
                                    'message': _t('Erro SAT: '),
                                    'comment': _t(result['excessao']),
                                });
                            }

                        },function(error){
                            if (error) {
                                self.pos.pos_widget.screen_selector.show_popup('error-traceback',{
                                    'message': _t('Erro SAT: '),
                                    'comment': error.data.message,
                                });
                                return;
                            }
                            self.receipt_queue.unshift(r)
                            self.receipt_queue.unshift(j)
                        });
                }
            }
            send_sat_job();
        },
        cancel_last_order: function(order){
            var self = this;
	        order['cnpj_software_house'] = self.pos.config.cnpj_software_house;
            self.message('cancelar_cfe',{ json: order },{ timeout: 5000 })
            .then(function(result){
                if (result){
                    var posOrderModel = new instance.web.Model('pos.order');
                    var posOrder = posOrderModel.call('refund', {'ids': result.order_id, 'dados': result})
                    .then(function (orders) {
                        self.pos.pos_widget.screen_selector.show_popup('error',{
                            message: _t('Venda Cancelada!'),
                            comment: _t('A venda foi cancelada com sucesso.'),
                        });
                        setTimeout(function () {
                            self.pos.pos_widget.posorderlist_screen.get_last_orders();
                            self.pos.pos_widget.screen_selector.back();
                        }, 4000);
                    });
                }else{
                    self.pos.pos_widget.screen_selector.show_popup('error-traceback',{
                        'message': _t('Erro SAT: '),
                        'comment': _t(result['excessao']),
                    });
                }

            },function(error){
                if (error) {
                    self.pos.pos_widget.screen_selector.show_popup('error-traceback',{
                        'message': _t('Erro SAT: '),
                        'comment': error.data.message,
                    });
                    return;
                }
            });
        },
        reprint_cfe: function(order){
            var self = this;

            self.message('reprint_cfe',{ json: order },{ timeout: 5000 })
            .then(function(result){
                return;
            },function(error){
                if (error) {
                    self.pos.pos_widget.screen_selector.show_popup('error-traceback',{
                        'message': _t('Erro SAT: '),
                        'comment': error.data.message,
                    });
                    return;
                }
            });
        }
    });

    module.ProxyDevice = module.ProxyDevice.extend({
        keepalive: function(){
            var self = this;
            if(!this.keptalive){
                this.keptalive = true;
                function status(){
                    self.connection.rpc('/hw_proxy/status_json',{},{timeout:2500})
                        .then(function(driver_status){
                            if(!driver_status.hasOwnProperty("satcfe")){
                                self.pos.proxy.init_sat(self.pos.config);
                            } else {
                                self.set_connection_status('connected',driver_status);
                            }
                        },function(){
                            if(self.get('status').driver_statusstatus !== 'connecting'){
                                self.set_connection_status('disconnected');
                            }
                        }).always(function(){
                            setTimeout(status,5000);
                        });
                }
                status();
            };
        }
    });
}
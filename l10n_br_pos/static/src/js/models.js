/******************************************************************************
 *    Point Of Sale - L10n Brazil Localization for POS Odoo
 *    Copyright (C) 2016 KMEE INFORMATICA LTDA (http://www.kmee.com.br)
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

function l10n_br_pos_models(instance, module) {
    var QWeb = instance.web.qweb;
    var _t = instance.web._t;
    /**
     * Extend the POS model
     */
    var PosModelParent = module.PosModel;
    module.PosModel = module.PosModel.extend({
        /**
         * @param session
         * @param attributes
         */
        initialize: function (session, attributes) {
            PosModelParent.prototype.initialize.apply(this, arguments);
            arrange_elements(this);
            this.models.push({
                model: 'res.country.state',
                fields: ['name', 'country_id'],
                loaded: function (self, states) {
                    self.company.state = null;
                    self.states = states;
//                    for (var i = 0; i < states.length; i++) {
//                        if(states[i].country_id[0] == 32){
//                            self.states.push(states[i]);
//                        }
//                        if(states[i].id === self.company.state_id[0]){
//                            self.company.state = states[i].id;
//                        }
//                    }
                }
            });
            this.models.push({
                model: 'l10n_br_base.city',
                fields: ['name', 'state_id'],
                loaded: function (self, cities) {
                    self.company.city = null;
                    self.cities = [];
//                    for (var i = 0; i < cities.length; i++) {
//                        if(cities[i].state_id[0] == 79){
//                            self.cities.push(cities[i]);
//                        }
//                    }
                }
            });
            this.models.push({
                model: 'pos.config',
                fields: [],
                domain: function (self) {
                    return [['id', '=', self.pos_session.config_id[0]]];
                },
                loaded: function (self, configs) {
                    self.config = configs[0];
                    self.config.use_proxy = self.config.iface_payment_terminal ||
                        self.config.iface_electronic_scale ||
                        self.config.iface_print_via_proxy ||
                        self.config.iface_scan_via_proxy ||
                        self.config.iface_cashdrawer ||
                        self.config.iface_sat_via_proxy;

                    self.barcode_reader.add_barcode_patterns({
                        'product': self.config.barcode_product,
                        'cashier': self.config.barcode_cashier,
                        'client': self.config.barcode_customer,
                        'weight': self.config.barcode_weight,
                        'discount': self.config.barcode_discount,
                        'price': self.config.barcode_price,
                    });

                    if (self.config.company_id[0] !== self.user.company_id[0]) {
                        throw new Error(_t("Error: The Point of Sale User must belong to the same company as the Point of Sale. You are probably trying to load the point of sale as an administrator in a multi-company setup, with the administrator account set to the wrong company."));
                    }
                }
            });
            this.models.push({
                model:  'res.partner',
                fields: ['name', 'cnpj_cpf', 'street','city','state_id','country_id','vat','phone','zip','mobile','email','ean13','write_date'],
                domain: [['customer','=',true]],
                loaded: function(self,partners){
                    self.partners = partners;
                    self.db.partner_by_id = [];
                    self.db.partner_sorted = [];
                    self.db.add_partners(partners);
                }
            });
            this.models.push({
                model: 'res.company',
                fields: [
                    'ambiente_sat',
                    'cnpj_cpf',
                    'inscr_est',
                    'currency_id',
                    'email',
                    'website',
                    'company_registry',
                    'vat',
                    'name',
                    'phone',
                    'partner_id',
                    'country_id',
                    'tax_calculation_rounding_method'],
                ids: function (self) {
                    return [self.user.company_id[0]]
                },
                loaded: function (self, companies) {
                    self.company = companies[0];
                },
            });

        },

        /**
         * find model based on name
         * @param model_name
         * @returns {{}}
         */
        find_model: function (model_name) {
            var self = this;
            var lookup = {};
            for (var i = 0, len = self.models.length; i < len; i++) {
                if (self.models[i].model === model_name) {
                    lookup[i] = self.models[i]
                }
            }
            return lookup
        },
//        PosModelParent.models.push({
//            model:  'res.country.state',
//            fields: ['name'],
//            loaded: function(self,states){
//                self.state = states;
//                self.company.state = null;
//                for (var i = 0; i < states.length; i++) {
//                    if (states[i].id === self.company.state_id[0]){
//                        self.company.state = states[i];
//                    }
//                }
//            }
//        });
        cancel_pos_order: function (chave_cfe) {
            var self = this;

            var posOrderModel = new instance.web.Model('pos.order');
            var posOrder = posOrderModel.call('cancel_last_order', {'chave_cfe': chave_cfe})
                .then(function (orders) {
                    console.log("cancel_pos_order");
                    console.log(self);
                    self.pos_widget.screen_selector.show_popup('error', {
                        message: _t('Venda Cancelada!'),
                        comment: _t('A venda foi cancelada com sucesso.'),
                    });
                });
        },
    });

    var PosOrderSuper = module.Order;

    module.Order = module.Order.extend({
        get_return_cfe: function () {
            return this.cfe_return;
        },
        set_return_cfe: function (xml) {
            this.cfe_return = xml;
        },
        get_chave_cfe: function () {
            return this.chave_cfe;
        },
        set_chave_cfe: function (chavecfe) {
            this.chave_cfe = chavecfe;
        },
        get_num_sessao_sat: function () {
            return this.num_sessao_sat;
        },
        set_num_sessao_sat: function (num_sessao_sat) {
            this.num_sessao_sat = num_sessao_sat;
        },
        export_for_printing: function () {
            var client = this.get('client');

            var status = this.pos.proxy.get('status');
            var sat_status = status.drivers.satcfe ? status.drivers.satcfe.status : false;
            if( sat_status == 'connected') {
            // Refactory
                if (this.pos.company.ambiente_sat == "homologacao") {
                    company.cnpj = this.pos.config.cnpj_homologacao;
                    company.ie = this.pos.config.ie_homologacao;
                    company.cnpj_software_house = this.pos.config.cnpj_software_house;
                } else {
                    company.cnpj = this.pos.company.cnpj_cpf;
                    company.ie = this.pos.company.inscr_est;
                    company.cnpj_software_house = this.pos.config.cnpj_software_house;
                }

                var result = PosOrderSuper.prototype.export_for_printing.call(this);
                result['pos_session_id'] = this.pos.pos_session.id;
                result['client'] = client ? client.cnpj_cpf : null;
                result['company']['cnpj'] = company.cnpj;
                result['company']['ie'] = company.ie;
                result['company']['cnpj_software_house'] = company.cnpj_software_house;
                result['configs_sat']['sat_path'] = this.pos.config.sat_path;
                result['configs_sat']['numero_caixa'] = this.pos.config.numero_caixa;
                result['configs_sat']['cod_ativacao'] = this.pos.config.cod_ativacao;
                result['configs_sat']['impressora'] = this.pos.config.impressora;
                result['configs_sat']['printer_params'] = this.pos.config.printer_params;

                return result;
            }else{
                var result = PosOrderSuper.prototype.export_for_printing.call(this);
                result['pos_session_id'] = this.pos.pos_session.id;
                result['client'] = client ? client.cnpj_cpf : null;
                result['cfe_return'] = this.get_return_cfe() ? this.get_return_cfe() : false;
                result['num_sessao_sat'] = this.get_num_sessao_sat() ? this.get_num_sessao_sat() : false;
                result['chave_cfe'] = this.get_chave_cfe() ? this.get_chave_cfe() : false;

                return result;
            }
        },
        export_as_JSON: function () {
            var client = this.get('client');

            var status = this.pos.proxy.get('status');
            var sat_status = status.drivers.satcfe ? status.drivers.satcfe.status : false;
            if( sat_status == 'connected') {
                if (this.pos.company.ambiente_sat == "homologacao") {
                    company.cnpj = this.pos.config.cnpj_homologacao;
                    company.ie = this.pos.config.ie_homologacao;
                    company.cnpj_software_house = this.pos.config.cnpj_software_house;
                } else {
                    company.cnpj = this.pos.company.cnpj_cpf;
                    company.ie = this.pos.company.inscr_est;
                    company.cnpj_software_house = this.pos.config.cnpj_software_house;
                }

                var result = PosOrderSuper.prototype.export_as_JSON.call(this);
                result['company']['cnpj'] = company.cnpj;
                result['company']['ie'] = company.ie;
                result['company']['cnpj_software_house'] = company.cnpj_software_house;
                result['configs_sat']['sat_path'] = this.pos.config.sat_path;
                result['configs_sat']['numero_caixa'] = this.pos.config.numero_caixa;
                result['configs_sat']['cod_ativacao'] = this.pos.config.cod_ativacao;
                result['configs_sat']['impressora'] = this.pos.config.impressora;
                result['configs_sat']['printer_params'] = this.pos.config.printer_params;
                result['cfe_return'] = this.get_return_cfe() ? this.get_return_cfe() : false;
                result['num_sessao_sat'] = this.get_num_sessao_sat() ? this.get_num_sessao_sat() : false;
                result['chave_cfe'] = this.get_chave_cfe() ? this.get_chave_cfe() : false;

                return result;
            }else{
                var result = PosOrderSuper.prototype.export_as_JSON.call(this);
                result['cfe_return'] = this.get_return_cfe() ? this.get_return_cfe() : false;
                result['num_sessao_sat'] = this.get_num_sessao_sat() ? this.get_num_sessao_sat() : false;
                result['chave_cfe'] = this.get_chave_cfe() ? this.get_chave_cfe() : false;

                return result;
            }
        }
    });

    var PosPaymentlineSuper = module.Paymentline;

    module.Paymentline = module.Paymentline.extend({
        set_payment_term: function(payment_term){
            this.payment_term = payment_term;
        },
        get_payment_term: function(){
            return this.payment_term;
        },
        export_as_JSON: function() {
            var result = PosPaymentlineSuper.prototype.export_as_JSON.call(this);
            result['sat_payment_mode'] = this.cashregister.journal.sat_payment_mode;
            result['sat_card_accrediting'] = this.cashregister.journal.sat_card_accrediting;
            return result;
        },
        export_for_printing: function(){
            var result = PosPaymentlineSuper.prototype.export_for_printing.call(this);
            result['sat_payment_mode'] = this.cashregister.journal.sat_payment_mode;
            result['sat_card_accrediting'] = this.cashregister.journal.sat_card_accrediting;
            return result;
        }
    });

       function arrange_elements(pos_model) {
            var product_product_model = pos_model.find_model('product.product');
            if (_.size(product_product_model) == 1) {
                var res_partner_index =
                    parseInt(Object.keys(product_product_model)[0]);
                pos_model.models[res_partner_index].fields.push(
                    'fiscal_classification_id',
                    'origin',
                    'estimated_taxes',
                    'name'
                );
        }


        function arrange_elements(pos_model) {
            var account_journal_model = pos_model.find_model('account.journal');
            if (_.size(account_journal_model) == 1) {
                var account_journal_model =
                    parseInt(Object.keys(account_journal_model)[0]);
                pos_model.models[res_partner_index].fields.push(
                    'sat_payment_mode',
                    'sat_card_accrediting'
                );
            }

            /**
             * patch models to load some entities
             * @param pos_model
             */
            function arrange_elements(pos_model) {
                var res_partner_model = pos_model.find_model('res.partner');
                if (_.size(res_partner_model) == 1) {
                    var res_partner_index =
                        parseInt(Object.keys(res_partner_model)[0]);
                    pos_model.models[res_partner_index].fields.push(
                        'legal_name',
                        'cnpj_cpf',
                        'inscr_est',
                        'inscr_mun',
                        'suframa',
                        'district',
                        'number',
                        'country_id',
                        'state_id',
                        'l10n_br_city_id'
                    );
                }

                var res_company_model = pos_model.find_model('res.company');
                if (_.size(res_company_model) == 1) {
                    var res_company_index =
                        parseInt(Object.keys(res_company_model)[0]);
                    pos_model.models[res_company_index].fields.push(
                        'legal_name',
                        'cnpj_cpf',
                        'inscr_est',
                        'inscr_mun',
                        'suframa',
                        'district',
                        'number',
                        'country_id',
                        'state_id',
                        'l10n_br_city_id'
                    );
                }
                ;
            };
        };
    };
}
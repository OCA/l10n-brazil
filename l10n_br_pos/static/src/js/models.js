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
                model:  'res.country.state',
                fields: ['name', 'country_id'],
                loaded: function(self,states){
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
                model:  'l10n_br_base.city',
                fields: ['name', 'state_id'],
                loaded: function(self,cities){
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
                domain: function(self){ return [['id','=', self.pos_session.config_id[0]]]; },
                loaded: function(self,configs){
                    self.config = configs[0];
                    self.config.use_proxy = self.config.iface_payment_terminal ||
                                            self.config.iface_electronic_scale ||
                                            self.config.iface_print_via_proxy  ||
                                            self.config.iface_scan_via_proxy   ||
                                            self.config.iface_cashdrawer       ||
                                            self.config.iface_sat_via_proxy;

                    self.barcode_reader.add_barcode_patterns({
                        'product':  self.config.barcode_product,
                        'cashier':  self.config.barcode_cashier,
                        'client':   self.config.barcode_customer,
                        'weight':   self.config.barcode_weight,
                        'discount': self.config.barcode_discount,
                        'price':    self.config.barcode_price,
                    });

                    if (self.config.company_id[0] !== self.user.company_id[0]) {
                        throw new Error(_t("Error: The Point of Sale User must belong to the same company as the Point of Sale. You are probably trying to load the point of sale as an administrator in a multi-company setup, with the administrator account set to the wrong company."));
                    }
                }
            });

            this.models.push({
                model:  'res.company',
                fields: [ 'ambiente_sat', 'cnpj_cpf', 'inscr_est', 'currency_id', 'email', 'website', 'company_registry', 'vat', 'name', 'phone', 'partner_id' , 'country_id', 'tax_calculation_rounding_method'],
                ids:    function(self){ return [self.user.company_id[0]] },
                loaded: function(self,companies){ self.company = companies[0]; },
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
        cancel_pos_order: function(chave_cfe){
            var self = this;

            var posOrderModel = new instance.web.Model('pos.order');
            var posOrder = posOrderModel.call('cancel_last_order', {'chave_cfe': chave_cfe})
            .then(function (orders) {
                console.log("cancel_pos_order");
                console.log(self);
                self.pos_widget.screen_selector.show_popup('error',{
                    message: _t('Venda Cancelada!'),
                    comment: _t('A venda foi cancelada com sucesso.'),
                });
            });
        },
    });

    module.Order = module.Order.extend({
        initialize: function(attributes){
            Backbone.Model.prototype.initialize.apply(this, arguments);
            this.pos = attributes.pos;
            this.sequence_number = this.pos.pos_session.sequence_number++;
            this.uid =     this.generateUniqueId();
            this.set({
                creationDate:   new Date(),
                orderLines:     new module.OrderlineCollection(),
                paymentLines:   new module.PaymentlineCollection(),
                name:           _t("Order ") + this.uid,
                client:         null
            });
            this.selected_orderline   = undefined;
            this.selected_paymentline = undefined;
            this.screen_data = {};  // see ScreenSelector
            this.receipt_type = 'receipt';  // 'receipt' || 'invoice'
            this.temporary = attributes.temporary || false;
            this.cfe_return = null;
            this.num_sessao_sat = null;
            this.chave_cfe = null;
            return this;
        },
        get_return_cfe: function(){
            return this.cfe_return;
        },
        set_return_cfe: function(xml){
            this.cfe_return = xml;
        },
        get_chave_cfe: function(){
            return this.chave_cfe;
        },
        set_chave_cfe: function(chavecfe){
            this.chave_cfe = chavecfe;
        },
        get_num_sessao_sat: function(){
            return this.num_sessao_sat;
        },
        set_num_sessao_sat: function(num_sessao_sat){
            this.num_sessao_sat = num_sessao_sat;
        },
        export_for_printing: function(){
            var orderlines = [];
            this.get('orderLines').each(function(orderline){
                orderlines.push(orderline.export_for_printing());
            });

            var paymentlines = [];
            this.get('paymentLines').each(function(paymentline){
                paymentlines.push(paymentline.export_for_printing());
            });
            var client  = this.get('client');
            var cashier = this.pos.cashier || this.pos.user;
            var company = this.pos.company;
            var shop    = this.pos.shop;
            var date = new Date();
            // Refactory
            if (this.pos.company.ambiente_sat == "homologacao"){
                company.cnpj = this.pos.config.cnpj_homologacao;
                company.ie = this.pos.config.ie_homologacao;
                company.cnpj_software_house = this.pos.config.cnpj_software_house;
            }else{
                company.cnpj = this.pos.company.cnpj_cpf;
                company.ie = this.pos.company.inscr_est;
                company.cnpj_software_house = this.pos.config.cnpj_software_house;
            }

            return {
                orderlines: orderlines,
                paymentlines: paymentlines,
                subtotal: this.getSubtotal(),
                total_with_tax: this.getTotalTaxIncluded(),
                total_without_tax: this.getTotalTaxExcluded(),
                total_tax: this.getTax(),
                total_paid: this.getPaidTotal(),
                total_discount: this.getDiscountTotal(),
                tax_details: this.getTaxDetails(),
                change: this.getChange(),
                name : this.getName(),
                client: client ? client.cnpj_cpf : null ,
                invoice_id: null,   //TODO
                cashier: cashier ? cashier.name : null,
                header: this.pos.config.receipt_header || '',
                footer: this.pos.config.receipt_footer || '',
                precision: {
                    price: 2,
                    money: 2,
                    quantity: 3,
                },
                date: {
                    year: date.getFullYear(),
                    month: date.getMonth(),
                    date: date.getDate(),       // day of the month
                    day: date.getDay(),         // day of the week
                    hour: date.getHours(),
                    minute: date.getMinutes() ,
                    isostring: date.toISOString(),
                    localestring: date.toLocaleString(),
                },
                company:{
                    email: company.email,
                    website: company.website,
                    company_registry: company.company_registry,
                    contact_address: company.partner_id[1],
                    vat: company.vat,
                    name: company.name,
                    phone: company.phone,
                    logo:  this.pos.company_logo_base64,
                    cnpj: company.cnpj,
                    ie: company.ie,
                    cnpj_software_house: company.cnpj_software_house,
                },
                shop:{
                    name: shop.name,
                },
                configs_sat: {
                    sat_path: this.pos.config.sat_path,
                    numero_caixa: this.pos.config.numero_caixa,
                    cod_ativacao: this.pos.config.cod_ativacao,
                    impressora: this.pos.config.impressora,
                    printer_params: this.pos.config.printer_params,
                },
                currency: this.pos.currency,
            };
        },
        export_as_JSON: function() {
            var orderLines, paymentLines;
            orderLines = [];
            (this.get('orderLines')).each(_.bind( function(item) {
                return orderLines.push([0, 0, item.export_as_JSON()]);
            }, this));
            paymentLines = [];
            (this.get('paymentLines')).each(_.bind( function(item) {
                return paymentLines.push([0, 0, item.export_as_JSON()]);
            }, this));
            return {
                name: this.getName(),
                amount_paid: this.getPaidTotal(),
                amount_total: this.getTotalTaxIncluded(),
                amount_tax: this.getTax(),
                amount_return: this.getChange(),
                lines: orderLines,
                statement_ids: paymentLines,
                pos_session_id: this.pos.pos_session.id,
                partner_id: this.get_client() ? this.get_client().id : false,
                user_id: this.pos.cashier ? this.pos.cashier.id : this.pos.user.id,
                uid: this.uid,
                sequence_number: this.sequence_number,
                cfe_return: this.get_return_cfe(),
                num_sessao_sat: this.get_num_sessao_sat(),
                chave_cfe: this.get_chave_cfe()
            };
        }
    });

    module.Orderline = module.Orderline.extend({
        //used to create a json of the ticket, to be sent to the printer
        export_for_printing: function(){
            return {
                quantity:           this.get_quantity(),
                unit_name:          this.get_unit().name,
                price:              this.get_unit_price(),
                discount:           this.get_discount(),
                product_name:       this.get_product().display_name,
                price_display :     this.get_display_price(),
                price_with_tax :    this.get_price_with_tax(),
                price_without_tax:  this.get_price_without_tax(),
                tax:                this.get_tax(),
                product_description:      this.get_product().description,
                product_description_sale: this.get_product().description_sale,
                product_default_code: this.get_product().default_code,
            };
        },
    });

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
    }
}

/******************************************************************************
*    Point Of Sale - L10n Brazil Localization for POS Odoo
*    Copyright (C) 2016 KMEE INFORMATICA LTDA (http://www.kmee.com.br)
*    @author Luiz Felipe do Divino <luiz.divino@kmee.com.br>
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

function l10n_br_pos_screens(instance, module) {
    var QWeb = instance.web.qweb;
    var _t = instance.web._t;

    module.HaveCpfCnpj = module.OrderWidget.include({
        template: 'PosWidget',

        init: function(parent, options){
            this._super(parent);
            var self = this;
        },
        renderElement: function() {
            var self = this;
            this._super();

            var partner = null;
            var isSave = null;

            this.el.querySelector('.btn-busca-cpf-cnpj').addEventListener('click',this.search_handler);
            $('.btn-busca-cpf-cnpj', this.el).click(function(e){
                if (self.verificar_cpf_cnpj($('.busca-cpf-cnpj').val())){
                    partner = self.pos.db.get_partner_by_identification(self.pos.partners,$('.busca-cpf-cnpj').val());
                    self.old_client = partner;
                    self.new_client = self.old_client;
                    if (partner){
                        self.pos.get('selectedOrder').set_client(self.new_client);
                    }else{
                        if (self.pos.config.save_identity_automatic){
                            new_partner = {};
                            new_partner["name"] = $('.busca-cpf-cnpj').val();
                            if (new_partner["name"].length > 11){
                                new_partner["is_company"] = true;
                            }
                            new_partner["cnpj_cpf"] = $('.busca-cpf-cnpj').val();
                            new_partner["property_account_receivable"] = 9;
                            new_partner["property_account_payable"] = 17;
                            isSave = self.save_client_details(new_partner);
                            if (isSave){
                                self.old_client = new_partner;
                                self.new_client = self.old_client;
                                self.pos.get('selectedOrder').set_client(self.new_client);
                            }
                        }
                    }
                } else {
                    self.pos_widget.screen_selector.show_popup('error',{
                        message: _t('CPF/CNPJ digitado esta incorreto!'),
                    });
                }
            });

         },
        save_client_details: function(partner) {
            var self = this;

            if (!partner.name) {
                this.pos_widget.screen_selector.show_popup('error',{
                    message: _t('A Customer Name Is Required'),
                });
                return;
            }

            new instance.web.Model('res.partner').call('create_from_ui',[partner]).then(function(partner_id){
                return true;
            },function(err,event){
                event.preventDefault();
                self.pos_widget.screen_selector.show_popup('error',{
                    'message':_t('Error: Could not Save Changes'),
                    'comment':_t('Your Internet connection is probably down.'),
                });
                return false;
            });


        },
        verificar_cpf_cnpj: function(documento){
            if (documento.length <= 11){
                var Soma;
                var Resto;
                Soma = 0;
                if (documento == "00000000000") return false;

                for (i=1; i<=9; i++) Soma = Soma + parseInt(documento.substring(i-1, i)) * (11 - i);
                Resto = (Soma * 10) % 11;

                if ((Resto == 10) || (Resto == 11))  Resto = 0;
                if (Resto != parseInt(documento.substring(9, 10)) ) return false;

                Soma = 0;
                for (i = 1; i <= 10; i++) Soma = Soma + parseInt(documento.substring(i-1, i)) * (12 - i);
                Resto = (Soma * 10) % 11;

                if ((Resto == 10) || (Resto == 11))  Resto = 0;
                if (Resto != parseInt(documento.substring(10, 11) ) ) return false;
                return true;
            }else{
                documento = documento.replace(/[^\d]+/g,'');

                if(documento == '') return false;

                if (documento.length != 14)
                    return false;

                // Elimina CNPJs invalidos conhecidos
                if (documento == "00000000000000" ||
                    documento == "11111111111111" ||
                    documento == "22222222222222" ||
                    documento == "33333333333333" ||
                    documento == "44444444444444" ||
                    documento == "55555555555555" ||
                    documento == "66666666666666" ||
                    documento == "77777777777777" ||
                    documento == "88888888888888" ||
                    documento == "99999999999999")
                    return false;

                // Valida DVs
                tamanho = documento.length - 2
                numeros = documento.substring(0,tamanho);
                digitos = documento.substring(tamanho);
                soma = 0;
                pos = tamanho - 7;
                for (i = tamanho; i >= 1; i--) {
                  soma += numeros.charAt(tamanho - i) * pos--;
                  if (pos < 2)
                        pos = 9;
                }
                resultado = soma % 11 < 2 ? 0 : 11 - soma % 11;
                if (resultado != digitos.charAt(0))
                    return false;

                tamanho = tamanho + 1;
                numeros = documento.substring(0,tamanho);
                soma = 0;
                pos = tamanho - 7;
                for (i = tamanho; i >= 1; i--) {
                  soma += numeros.charAt(tamanho - i) * pos--;
                  if (pos < 2)
                        pos = 9;
                }
                resultado = soma % 11 < 2 ? 0 : 11 - soma % 11;
                if (resultado != digitos.charAt(1))
                      return false;

                return true;
            }

        }
    });

    module.PaypadWidget = module.PosBaseWidget.extend({
        template: 'PaypadWidget',
        renderElement: function() {
            var self = this;
            this._super();

            var button = new module.PosOrderListButtonWidget(self,{
                pos: self.pos,
                pos_widget : self.pos_widget,
            });
            button.appendTo(self.$el);

            _.each(this.pos.cashregisters,function(cashregister) {
                var button = new module.PaypadButtonWidget(self,{
                    pos: self.pos,
                    pos_widget : self.pos_widget,
                    cashregister: cashregister,
                });
                button.appendTo(self.$el);
            });

        }
    });

    module.PosOrderListButtonWidget = module.PosBaseWidget.extend({
        template: 'PosOrderListButtonWidget',
        init: function(parent, options){
            this._super(parent, options);
            this.cashregister = options.cashregister;
        },
        renderElement: function() {
            var self = this;
            this._super();

            this.$el.click(function(){
                var ss = self.pos.pos_widget.screen_selector;
                if(ss.get_current_screen() === 'posordertlist'){
                    ss.back();
                }else if (ss.get_current_screen() !== 'receipt'){
                    ss.set_current_screen('posordertlist');
                }
            });
        },
    });

    module.PaymentScreenWidget = module.PaymentScreenWidget.extend({
        validate_order: function(options) {
            var self = this;
            options = options || {};

            var currentOrder = this.pos.get('selectedOrder');

            if(currentOrder.get('orderLines').models.length === 0){
                this.pos_widget.screen_selector.show_popup('error',{
                    'message': _t('Empty Order'),
                    'comment': _t('There must be at least one product in your order before it can be validated'),
                });
                return;
            }

            var plines = currentOrder.get('paymentLines').models;
            for (var i = 0; i < plines.length; i++) {
                if (plines[i].get_type() === 'bank' && plines[i].get_amount() < 0) {
                    this.pos_widget.screen_selector.show_popup('error',{
                        'message': _t('Negative Bank Payment'),
                        'comment': _t('You cannot have a negative amount in a Bank payment. Use a cash payment method to return money to the customer.'),
                    });
                    return;
                }
            }

            if(!this.is_paid()){
                return;
            }

            // The exact amount must be paid if there is no cash payment method defined.
            if (Math.abs(currentOrder.getTotalTaxIncluded() - currentOrder.getPaidTotal()) > 0.00001) {
                var cash = false;
                for (var i = 0; i < this.pos.cashregisters.length; i++) {
                    cash = cash || (this.pos.cashregisters[i].journal.type === 'cash');
                }
                if (!cash) {
                    this.pos_widget.screen_selector.show_popup('error',{
                        message: _t('Cannot return change without a cash payment method'),
                        comment: _t('There is no cash payment method available in this point of sale to handle the change.\n\n Please pay the exact amount or add a cash payment method in the point of sale configuration'),
                    });
                    return;
                }
            }

            if (this.pos.config.iface_cashdrawer) {
                    this.pos.proxy.open_cashbox();
            }
            var status = this.pos.proxy.get('status');
            var sat_status = status.drivers.satcfe ? status.drivers.satcfe.status : false;
            if( sat_status == 'connected'){
                if(options.invoice){
                    // deactivate the validation button while we try to send the order
                    this.pos_widget.action_bar.set_button_disabled('validation',true);
                    this.pos_widget.action_bar.set_button_disabled('invoice',true);

                    var invoiced = this.pos.push_and_invoice_order(currentOrder);

                    invoiced.fail(function(error){
                        if(error === 'error-no-client'){
                            self.pos_widget.screen_selector.show_popup('error',{
                                message: _t('An anonymous order cannot be invoiced'),
                                comment: _t('Please select a client for this order. This can be done by clicking the order tab'),
                            });
                        }else{
                            self.pos_widget.screen_selector.show_popup('error',{
                                message: _t('The order could not be sent'),
                                comment: _t('Check your internet connection and try again.'),
                            });
                        }
                        self.pos_widget.action_bar.set_button_disabled('validation',false);
                        self.pos_widget.action_bar.set_button_disabled('invoice',false);
                    });

                    invoiced.done(function(){
                        self.pos_widget.action_bar.set_button_disabled('validation',false);
                        self.pos_widget.action_bar.set_button_disabled('invoice',false);
                        self.pos.get('selectedOrder').destroy();
                    });

                }else{
                    var retorno_sat = {};
                    if(this.pos.config.iface_sat_via_proxy){
                        var receipt = currentOrder.export_for_printing();
                        var json = currentOrder.export_for_printing();
                        this.pos.proxy.send_order_sat(
                            currentOrder,
                            QWeb.render('XmlReceipt',{
                            receipt: receipt, widget: self,
                        }), json);
                    }else{
                        this.pos.push_order(currentOrder);
                    }

                    if(this.pos.config.iface_print_via_proxy){
                        var receipt = currentOrder.export_for_printing();
                        this.pos.proxy.print_receipt(
                            QWeb.render('XmlReceipt',{
                            receipt: receipt, widget: self,
                        }));
                        this.pos.get('selectedOrder').destroy();    //finish order and go back to scan screen
                    }else{
                        this.pos_widget.screen_selector.set_current_screen(this.next_screen);
                    }
                }
            }else{
                self.pos_widget.screen_selector.show_popup('error',{
                    message: _t('SAT n\u00e3o est\u00e1 conectado'),
                    comment: _t('Verifique se existe algum problema com o SAT e tente fazer a requisi\u00e7\u00e3o novamente.'),
                });
            }

            // hide onscreen (iOS) keyboard
            setTimeout(function(){
                document.activeElement.blur();
                $("input").blur();
            },250);
        },
    });

    module.PosOrderListScreenWidget = module.ScreenWidget.extend({
        template: 'PosOrderListScreenWidget',

        init: function(parent, options){
            this._super(parent, options);
        },
        show_leftpane: false,

        auto_back: true,

        show: function(){
            var self = this;
            this._super();

            this.renderElement();
            this.details_visible = false;
            this.old_client = this.pos.get('selectedOrder').get('client');
            this.new_client = this.old_client;

            this.$('.back').click(function(){
                self.pos_widget.screen_selector.back();
            });

            this.$('.next').click(function(){
                self.save_changes();
                self.pos_widget.screen_selector.back();
            });

            this.$('.new-customer').click(function(){
                self.display_client_details('edit',{
                    'country_id': self.pos.company.country_id,
                });
            });

            var partners = this.pos.db.get_partners_sorted(1000);
            this.render_list(partners);

            this.reload_partners();

            if( this.old_client ){
                this.display_client_details('show',this.old_client,0);
            }

            this.$('.client-list-contents').delegate('.client-line','click',function(event){
                self.line_select(event,$(this),parseInt($(this).data('id')));
            });

            var search_timeout = null;

            if(this.pos.config.iface_vkeyboard && this.pos_widget.onscreen_keyboard){
                this.pos_widget.onscreen_keyboard.connect(this.$('.searchbox input'));
            }

            this.$('.searchbox input').on('keyup',function(event){
                clearTimeout(search_timeout);

                var query = this.value;

                search_timeout = setTimeout(function(){
                    self.perform_search(query,event.which === 13);
                },70);
            });

            this.$('.searchbox .search-clear').click(function(){
                self.clear_search();
            });
        },
        barcode_client_action: function(code){
            if (this.editing_client) {
                this.$('.detail.barcode').val(code.code);
            } else if (this.pos.db.get_partner_by_ean13(code.code)) {
                this.display_client_details('show',this.pos.db.get_partner_by_ean13(code.code));
            }
        },
        perform_search: function(query, associate_result){
            if(query){
                var customers = this.pos.db.search_partner(query);
                this.display_client_details('hide');
                if ( associate_result && customers.length === 1){
                    this.new_client = customers[0];
                    this.save_changes();
                    this.pos_widget.screen_selector.back();
                }
                this.render_list(customers);
            }else{
                var customers = this.pos.db.get_partners_sorted();
                this.render_list(customers);
            }
        },
        clear_search: function(){
            var customers = this.pos.db.get_partners_sorted(1000);
            this.render_list(customers);
            this.$('.searchbox input')[0].value = '';
            this.$('.searchbox input').focus();
        },
        render_list: function(partners){
            var contents = this.$el[0].querySelector('.client-list-contents');
            contents.innerHTML = "";
            for(var i = 0, len = Math.min(partners.length,1000); i < len; i++){
                var partner    = partners[i];
                var clientline_html = QWeb.render('ClientLine',{widget: this, partner:partners[i]});
                var clientline = document.createElement('tbody');
                clientline.innerHTML = clientline_html;
                clientline = clientline.childNodes[1];

                if( partners === this.new_client ){
                    clientline.classList.add('highlight');
                }else{
                    clientline.classList.remove('highlight');
                }

                contents.appendChild(clientline);
            }
        },
        save_changes: function(){
            if( this.has_client_changed() ){
                this.pos.get('selectedOrder').set_client(this.new_client);
            }
        },
        has_client_changed: function(){
            if( this.old_client && this.new_client ){
                return this.old_client.id !== this.new_client.id;
            }else{
                return !!this.old_client !== !!this.new_client;
            }
        },
        toggle_save_button: function(){
            var $button = this.$('.button.next');
            if (this.editing_client) {
                $button.addClass('oe_hidden');
                return;
            } else if( this.new_client ){
                if( !this.old_client){
                    $button.text(_t('Set Customer'));
                }else{
                    $button.text(_t('Change Customer'));
                }
            }else{
                $button.text(_t('Deselect Customer'));
            }
            $button.toggleClass('oe_hidden',!this.has_client_changed());
        },
        line_select: function(event,$line,id){
            var partner = this.pos.db.get_partner_by_id(id);
            this.$('.client-list .lowlight').removeClass('lowlight');
            if ( $line.hasClass('highlight') ){
                $line.removeClass('highlight');
                $line.addClass('lowlight');
                this.display_client_details('hide',partner);
                this.new_client = null;
                this.toggle_save_button();
            }else{
                this.$('.client-list .highlight').removeClass('highlight');
                $line.addClass('highlight');
                var y = event.pageY - $line.parent().offset().top
                this.display_client_details('show',partner,y);
                this.new_client = partner;
                this.toggle_save_button();
            }
        },
        partner_icon_url: function(id){
            return '/web/binary/image?model=res.partner&id='+id+'&field=image_small';
        },

        // ui handle for the 'edit selected customer' action
        edit_client_details: function(partner) {
            this.display_client_details('edit',partner);
        },

        // ui handle for the 'cancel customer edit changes' action
        undo_client_details: function(partner) {
            if (!partner.id) {
                this.display_client_details('hide');
            } else {
                this.display_client_details('show',partner);
            }
        },

        // what happens when we save the changes on the client edit form -> we fetch the fields, sanitize them,
        // send them to the backend for update, and call saved_client_details() when the server tells us the
        // save was successfull.
        save_client_details: function(partner) {
            var self = this;

            var fields = {}
            this.$('.client-details-contents .detail').each(function(idx,el){
                fields[el.name] = el.value;
            });

            if (!fields.name) {
                this.pos_widget.screen_selector.show_popup('error',{
                    message: _t('A Customer Name Is Required'),
                });
                return;
            }

            if (this.uploaded_picture) {
                fields.image = this.uploaded_picture;
            }

            fields.id           = partner.id || false;
            fields.country_id   = fields.country_id || false;
            fields.ean13        = fields.ean13 ? this.pos.barcode_reader.sanitize_ean(fields.ean13) : false;

            new instance.web.Model('res.partner').call('create_from_ui',[fields]).then(function(partner_id){
                self.saved_client_details(partner_id);
            },function(err,event){
                event.preventDefault();
                self.pos_widget.screen_selector.show_popup('error',{
                    'message':_t('Error: Could not Save Changes'),
                    'comment':_t('Your Internet connection is probably down.'),
                });
            });
        },

        // what happens when we've just pushed modifications for a partner of id partner_id
        saved_client_details: function(partner_id){
            var self = this;
            this.reload_partners().then(function(){
                var partner = self.pos.db.get_partner_by_id(partner_id);
                if (partner) {
                    self.new_client = partner;
                    self.toggle_save_button();
                    self.display_client_details('show',partner);
                } else {
                    // should never happen, because create_from_ui must return the id of the partner it
                    // has created, and reload_partner() must have loaded the newly created partner.
                    self.display_client_details('hide');
                }
            });
        },

        // resizes an image, keeping the aspect ratio intact,
        // the resize is useful to avoid sending 12Mpixels jpegs
        // over a wireless connection.
        resize_image_to_dataurl: function(img, maxwidth, maxheight, callback){
            img.onload = function(){
                var png = new Image();
                var canvas = document.createElement('canvas');
                var ctx    = canvas.getContext('2d');
                var ratio  = 1;

                if (img.width > maxwidth) {
                    ratio = maxwidth / img.width;
                }
                if (img.height * ratio > maxheight) {
                    ratio = maxheight / img.height;
                }
                var width  = Math.floor(img.width * ratio);
                var height = Math.floor(img.height * ratio);

                canvas.width  = width;
                canvas.height = height;
                ctx.drawImage(img,0,0,width,height);

                var dataurl = canvas.toDataURL();
                callback(dataurl);
            }
        },

        // Loads and resizes a File that contains an image.
        // callback gets a dataurl in case of success.
        load_image_file: function(file, callback){
            var self = this;
            if (!file.type.match(/image.*/)) {
                this.pos_widget.screen_selector.show_popup('error',{
                    message:_t('Unsupported File Format'),
                    comment:_t('Only web-compatible Image formats such as .png or .jpeg are supported'),
                });
                return;
            }

            var reader = new FileReader();
            reader.onload = function(event){
                var dataurl = event.target.result;
                var img     = new Image();
                img.src = dataurl;
                self.resize_image_to_dataurl(img,800,600,callback);
            }
            reader.onerror = function(){
                self.pos_widget.screen_selector.show_popup('error',{
                    message:_t('Could Not Read Image'),
                    comment:_t('The provided file could not be read due to an unknown error'),
                });
            };
            reader.readAsDataURL(file);
        },

        // This fetches partner changes on the server, and in case of changes,
        // rerenders the affected views
        reload_partners: function(){
            var self = this;
            return this.pos.load_new_partners().then(function(){
                self.render_list(self.pos.db.get_partners_sorted(1000));

                // update the currently assigned client if it has been changed in db.
                var curr_client = self.pos.get_order().get_client();
                if (curr_client) {
                    self.pos.get_order().set_client(self.pos.db.get_partner_by_id(curr_client.id));
                }
            });
        },

        // Shows,hides or edit the customer details box :
        // visibility: 'show', 'hide' or 'edit'
        // partner:    the partner object to show or edit
        // clickpos:   the height of the click on the list (in pixel), used
        //             to maintain consistent scroll.
        display_client_details: function(visibility,partner,clickpos){
            var self = this;
            var contents = this.$('.client-details-contents');
            var parent   = this.$('.client-list').parent();
            var scroll   = parent.scrollTop();
            var height   = contents.height();

            contents.off('click','.button.edit');
            contents.off('click','.button.save');
            contents.off('click','.button.undo');
            contents.on('click','.button.edit',function(){ self.edit_client_details(partner); });
            contents.on('click','.button.save',function(){ self.save_client_details(partner); });
            contents.on('click','.button.undo',function(){ self.undo_client_details(partner); });
            this.editing_client = false;
            this.uploaded_picture = null;

            if(visibility === 'show'){
                contents.empty();
                contents.append($(QWeb.render('ClientDetails',{widget:this,partner:partner})));

                var new_height   = contents.height();

                if(!this.details_visible){
                    if(clickpos < scroll + new_height + 20 ){
                        parent.scrollTop( clickpos - 20 );
                    }else{
                        parent.scrollTop(parent.scrollTop() + new_height);
                    }
                }else{
                    parent.scrollTop(parent.scrollTop() - height + new_height);
                }

                this.details_visible = true;
                this.toggle_save_button();
            } else if (visibility === 'edit') {
                this.editing_client = true;
                contents.empty();
                contents.append($(QWeb.render('ClientDetailsEdit',{widget:this,partner:partner})));
                this.toggle_save_button();

                contents.find('.image-uploader').on('change',function(event){
                    self.load_image_file(event.target.files[0],function(res){
                        if (res) {
                            contents.find('.client-picture img, .client-picture .fa').remove();
                            contents.find('.client-picture').append("<img src='"+res+"'>");
                            contents.find('.detail.picture').remove();
                            self.uploaded_picture = res;
                        }
                    });
                });
            } else if (visibility === 'hide') {
                contents.empty();
                if( height > scroll ){
                    contents.css({height:height+'px'});
                    contents.animate({height:0},400,function(){
                        contents.css({height:''});
                    });
                }else{
                    parent.scrollTop( parent.scrollTop() - height);
                }
                this.details_visible = false;
                this.toggle_save_button();
            }
        },
        close: function(){
            this._super();
        },
    });
}
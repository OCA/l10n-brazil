odoo.define('l10n_br_website_sale.l10n_br_address', function (require) {
        'use strict';

        require('web.dom_ready');
        var ajax = require('web.ajax');

        if (!$('.checkout_autoformat').length) {
            return $.Deferred().reject("DOM doesn't contain '.checkout_autoformat'");
        }

        // var cleaveCNPJ = new Cleave('.input-cnpj-cpf', {
        //     blocks: [2, 3, 3, 4, 2],
        //     delimiters: ['.', '.', '-'],
        //     numericOnly: true,
        //     onValueChanged: function (e) {
        //         if (e.target.rawValue.length > 11) {
        //             this.properties['blocks'] = [2, 3, 3, 4, 2];
        //             this.properties['delimiters'] = ['.', '.', '/', '-'];
        //         } else {
        //             this.properties['blocks'] = [3, 3, 3, 3];
        //             this.properties['delimiters'] = ['.', '.', '-'];
        //         }
        //     }
        // });

        var cleaveZipCode = new Cleave('.input-zipcode', {
            blocks: [5, 3],
            delimiter: '-',
            numericOnly: true,
        });

        if ($('.checkout_autoformat').length) {
            var state_options = $(
                "select[name='city_id']:enabled option:not(:first)");
            $('.checkout_autoformat').on(
                'change', "select[name='state_id']", function () {
                    if (!$("#state_id").val()) {
                        return;
                    }
                    ajax.jsonRpc("/shop/state_infos/" + $("#state_id").val(), 'call')
                        .then(function (data) {
                        // placeholder phone_code
                        //$("input[name='phone']").attr('placeholder', data.phone_code !== 0 ? '+'+ data.phone_code : '');

                        // populate states and display
                        var selectCities = $("select[name='city_id']");
                        // dont reload state at first loading (done in qweb)
                        if (selectCities.data('init') === 0 || selectCities.find('option').length === 1) {
                            if (data.cities.length) {
                                // selectCities.html('');
                                _.each(data.cities, function (x) {
                                    var opt = $('<option>').text(x[1])
                                        .attr('value', x[0])
                                        .attr('data-code', x[2]);
                                    selectCities.append(opt);
                                });
                                selectCities.parent('div').show();
                                if (!$("select[name='city_id']").val()) {
                                    $('input[name="zip"]').change();
                                }
                            } else {
                                selectCities.val('').parent('div').hide();
                            }
                            selectCities.data('init', 0);
                        } else {
                            selectCities.data('init', 0);
                        }
                    })
                });
            // $('.checkout_autoformat').find("select[name='state_id']").change();
            $('.checkout_autoformat').on('change', "input[name='zip']",
                function () {
                    var vals = {zipcode: $('input[name="zip"]').val()};
                    console.log("Changing ZIP");
                    ajax.jsonRpc("/l10n_br/zip_search", 'call', vals)
                        .then(function (data) {
                            if (data.error) {
                                // TODO: Retornar nos campos error e error_message
                                console.log('Falha ao consultar cep');
                            } else {
                                $('input[name="district"]').val(data.district);
                                $('input[name="street"]').val(data.street);
                                $('select[name="state_id"]').val(data.state_id);
                                $('select[name="state_id"]').change();
                                $('select[name="city_id"]').val(data.city_id);
                                $('select[name="city_id"]').change();
                            }
                        });
                });
        }

    }
);

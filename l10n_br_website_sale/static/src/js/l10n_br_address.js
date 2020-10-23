odoo.define('l10n_br_website_sale.l10n_br_address', function (require) {
    'use strict';

    require('web.dom_ready');
    var ajax = require('web.ajax');

    if (!$('.checkout_autoformat').length) {
        return $.Deferred().reject("DOM doesn't contain" +
            " '.checkout_autoformat'");
    }

    if ($('#input_cnpj_cpf').length) {
        var cleaveCNPJ = new Cleave('#input_cnpj_cpf', {
            blocks: [2, 3, 3, 4, 2],
            delimiters: ['.', '.', '-'],
            numericOnly: true,
            onValueChanged: function (e) {
                if (e.target.rawValue.length > 11) {
                    this.properties['blocks'] = [2, 3, 3, 4, 2];
                    this.properties['delimiters'] = ['.', '.', '/', '-'];
                } else {
                    this.properties['blocks'] = [3, 3, 3, 3];
                    this.properties['delimiters'] = ['.', '.', '-'];
                }
            }
        });
    }

    var cleaveZipCode = new Cleave('.input-zipcode', {
        blocks: [5, 3],
        delimiter: '-',
        numericOnly: true,
    });

    if ($('.checkout_autoformat').length) {
        var state_options = $(
            "select[name='city_id']:enabled option:not(:first)");
        $('.checkout_autoformat').on(
            'change',
            "select[name='country_id']",
            function () {
                var country_id = $("select[name='country_id']") || false;
                if(country_id) {
                    if(country_id.val() == 31) {
                        $("input[name='city']").parent('div').hide();
                        $("select[name='city_id']").parent('div').show();
                    } else {
                        $("select[name='city_id']").parent('div').hide();
                        $("input[name='city']").parent('div').show();
                    }
                }
            });
        $('.checkout_autoformat').on(
            'change',
            "select[name='state_id']",
            function () {
                if (!$("#state_id").val()) {
                    return;
                }
                ajax.jsonRpc(
                    "/shop/state_infos/" + $("#state_id").val(),
                    'call').then(function (data) {
                        // populate states and display
                        var selectCities = $("select[name='city_id']");
                        var zip_city = $("select[name='city_id']")[0].val;
                        // dont reload state at first loading (done in qweb)
                        if (selectCities.data('init') === 0 || selectCities
                            .find('option').length === 1) {
                            if (data.cities.length) {
                                // selectCities.html('');
                                _.each(data.cities, function (x) {
                                    var opt = $('<option>').text(x[1])
                                        .attr('value', x[0])
                                        .attr('data-code', x[2]);
                                    selectCities.append(opt);
                                });
                                selectCities.parent('div').show();
                                $("input[name='city']").parent('div').hide();
                                $("select[name='city_id']").val(zip_city)
                                // if (!$("select[name='city_id']").val()) {
                                //     $('input[name="zip"]').change();
                                // }
                            } else {
                                selectCities.val('').parent('div')
                                    .hide();
                                $("input[name='city']").parent('div').show();
                            }
                            selectCities.data('init', 0);
                        } else {
                            selectCities.data('init', 0);
                        }
                });
            }
        );
        $('.checkout_autoformat').on(
            'change',
            "input[name='zip']",
            function () {
                var vals = {zipcode: $('input[name="zip"]').val()};
                console.log("Changing ZIP");
                $('a:contains("Next")').attr('display: none !important;')
                ajax.jsonRpc("/l10n_br/zip_search_public", 'call', vals).then(function (data) {
                    if (data.error) {
                        // todo: Retornar nos campos error e error_message
                        console.log('Falha ao consultar cep');
                    } else {
                        $('input[name="district"]').val(data.district);
                        $('input[name="street"]').val(data.street);
                        $('select[name="city_id"]').val(data.city_id);
                        $('select[name="city_id"]').change();
                        $('select[name="city_id"]')[0].val = data.city_id;
                        $('select[name="state_id"]').val(data.state_id);
                        $('select[name="state_id"]').change();
                        $('a:contains("Next")').attr('display: block !important;')
                    }
                });
            }
        );
    }
});

/* eslint no-unused-vars: "off", no-undef: "off" */

odoo.define("l10n_br_website_sale.l10n_br_address", function (require) {
    "use strict";

    require("web.dom_ready");
    var ajax = require("web.ajax");

    var $checkout_autoformat_selector = $(".checkout_autoformat");

    if (!$checkout_autoformat_selector.length) {
        return $.Deferred().reject("DOM doesn't contain '.checkout_autoformat'");
    }

    function formatCpfCnpj(inputValue) {
        // Remove non-numeric characters
        let value = inputValue.replace(/\D/g, "");

        // Truncate the value to 11 digits if it's more than 11 and less than 14
        if (value.length > 11 && value.length < 14) {
            value = value.substring(0, 11);
        }
        // Truncate the value to 14 digits if it's 14 or more
        else if (value.length >= 14) {
            value = value.substring(0, 14);
        }

        if (value.length <= 11) {
            // Format as CPF
            value = value.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, "$1.$2.$3-$4");
        } else {
            // Format as CNPJ
            value = value.replace(
                /(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})/,
                "$1.$2.$3/$4-$5"
            );
        }

        return value;
    }

    $("#input_cnpj_cpf").on("blur", function () {
        var value = $(this).val();
        var formattedValue = formatCpfCnpj(value);
        $(this).val(formattedValue);
    });

    var zip_cleave = new Cleave(".input-zipcode", {
        blocks: [5, 3],
        delimiter: "-",
        numericOnly: true,
    });

    if ($checkout_autoformat_selector.length) {
        $checkout_autoformat_selector.on(
            "change",
            "select[name='country_id']",
            function () {
                var country_id = $("select[name='country_id']") || false;

                ajax.jsonRpc("/shop/country_infos/" + country_id.val(), "call", {
                    mode: $("#country_id").attr("mode"),
                }).then(function (data) {
                    if (data.country_code) {
                        setTimeout(() => {
                            if (data.country_code === "BR") {
                                $("input[name='city']").parent("div").hide();
                                $("select[name='city_id']").parent("div").show();
                            } else {
                                $("select[name='city_id']").parent("div").hide();
                                $("input[name='city']").parent("div").show();
                            }
                        }, 1000);
                    }
                });
            }
        );
        $checkout_autoformat_selector.on(
            "change",
            "select[name='state_id']",
            function () {
                var state_id = $("#state_id").val();
                if (!state_id) {
                    return;
                }
                ajax.jsonRpc("/shop/state_infos/" + state_id, "call").then(function (
                    data
                ) {
                    var city_id_selector = $("select[name='city_id']");
                    city_id_selector.empty();
                    if (data.cities.length) {
                        data.cities.forEach(function (city) {
                            city_id_selector.append(
                                new Option(city[1], city[0], false, false)
                            );
                        });
                        city_id_selector.parent("div").show();
                        $("input[name='city']").parent("div").hide();
                    } else {
                        city_id_selector.parent("div").hide();
                        $("input[name='city']").parent("div").show();
                    }
                });
            }
        );
        $checkout_autoformat_selector.on("change", "input[name='zip']", function () {
            var vals = {zipcode: $('input[name="zip"]').val()};
            console.log("Changing ZIP code");
            $('a:contains("Next")').css("display", "none");
            ajax.jsonRpc("/l10n_br/zip_search_public", "call", vals).then(function (
                data
            ) {
                if (data.error) {
                    console.log("Failed to query zip code");
                } else {
                    var state_id_selector = $('select[name="state_id"]');
                    var city_id_selector = $('select[name="city_id"]');
                    // Set the district and street name based on the ZIP code data
                    $('input[name="district"]').val(data.district);
                    $('input[name="street_name"]').val(data.street_name);
                    // Set the value of the state selector and trigger its change event
                    state_id_selector.val(data.state_id).change();
                    // Wait for the city selector to be populated, then set its value and trigger its change event
                    setTimeout(() => {
                        city_id_selector.val(data.city_id).change();
                    }, 1000);
                    $('a:contains("Next")').css("display", "block");
                }
            });
        });
    }
});

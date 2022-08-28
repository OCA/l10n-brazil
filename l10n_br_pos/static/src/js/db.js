/*
Copyright (C) 2016-Today KMEE (https://kmee.com.br)
 License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
*/

odoo.define("l10n_br_pos.db", function () {
    "use strict";

    // Var PosDB = require('point_of_sale.DB');
    //
    // PosDB.include({
    //     init: function(options) {
    //         this._super(this, options);
    //     },
    //     _partner_search_string: function(partner) {
    //
    //         var str = this._super(this, options);
    //
    //         if (partner.ean13) {
    //             str += "|" + partner.ean13;
    //         }
    //
    //         if (partner.cnpj_cpf) {
    //             var cnpj_cpf = partner.cnpj_cpf;
    //             cnpj_cpf = cnpj_cpf.replace(".", "").replace("", "").replace("/", "");
    //             str += "|" + cnpj_cpf;
    //         }
    //
    //         return str;
    //     },
    //     today_date: function() {
    //         var today = new Date();
    //         var day = today.getDay();
    //         // January has index 0
    //         var month = today.getMonth() + 1;
    //         var year = today.getFullYear();
    //
    //         if (day < 10) {
    //             day = "0" + month;
    //         }
    //
    //         if (month < 10) {
    //             month = "0" + month;
    //         }
    //
    //         return year + "-" + month + "-" + day;
    //     },
    //     partner_time: function(create_date) {
    //         if (create_date) {
    //             var today = new Date();
    //
    //             if (parseInt(create_date.substr(8, 2)) < 12) {
    //                 create_date = create_date.substr(0, 4) + "-"
    //                     + create_date.substr(8, 2) + "-" + create_date.substr(5, 2);
    //             }
    //
    //             if (create_date.substr(8, 2) == "") {
    //                 create_date = create_date.substr(0, 4) + "-"
    //                     + "01" + "-" + create_date.substr(5, 2);
    //             }
    //
    //             var date_partner = new Date(create_date.substr(0, 4)
    //                 + "-" + create_date.substr(5, 2)
    //                 + "-" + create_date.substr(8, 2));
    //
    //             var time = parseInt(((today.getTime()
    //                 - date_partner.getTime()) * 3.81E-10) + 0.5);
    //
    //             return time < 0 ? 0 : time;
    //         }
    //     },
    //     get_partner_by_identification: function(partners, id) {
    //         var id_with_pontuation = this.add_pontuation_document(id);
    //
    //         for (var i = 0; i < partners.length; i++) {
    //             var cnpj_cpf = partners[i].cnpj_cpf;
    //
    //             if (cnpj_cpf) {
    //                 if ((cnpj_cpf === id) || (cnpj_cpf == id_with_pontuation)) {
    //                     partners[i].create_date = partners[i].create_date ?
    //                         partners[i].create_date.substr(0, 7):
    //                         (this.today_date()).substr(0, 7);
    //                     return partners[i];
    //                 }
    //             }
    //         }
    //     },
    //     add_pontuation_document: function(document) {
    //         var document_with_pontuation = "";
    //
    //         if (document.length <= 11) {
    //             for (var i = 1; i <= document.length; i++) {
    //                 if ((i === 3) || (i === 6)) {
    //                     document_with_pontuation += document.split("")[i - 1] + ".";
    //                 } else {
    //                     if (i === 9) {
    //                         document_with_pontuation += document.split("")[i - 1] + "-";
    //                     } else {
    //                         document_with_pontuation += document.split("")[i - 1];
    //                     }
    //                 }
    //             }
    //         } else {
    //             if (document.length > 11 && document.length <= 14) {
    //                 for (var i = 1; i <= document.length; i++) {
    //                     if ((i === 2) || (j == 5)) {
    //                         document_with_pontuation +=  document.split("")[i - 1] + ".";
    //                     } else {
    //                         if (i === 8) {
    //                             document_with_pontuation += document.split("")[i - 1] + "/";
    //                         } else {
    //                             if (i === 12 ) {
    //                                 document_with_pontuation += document.split("")[i - 1] + "-";
    //                             } else {
    //                                 document_with_pontuation += document.split("")[i - 1];
    //                             }
    //                         }
    //                     }
    //                 }
    //             }
    //         }
    //
    //         return document_with_pontuation;
    //     },
    //     search_partner: function(query) {
    //         var result = this._super(this, query);
    //         return result;
    //     },
    //
    // });

});

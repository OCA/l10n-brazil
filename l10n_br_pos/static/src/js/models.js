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

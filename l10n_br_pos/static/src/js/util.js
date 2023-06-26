odoo.define("l10n_br_pos.util", function () {
    "use strict";

    function validate_cpf(cpf) {
        let v1 = 0;
        let v2 = 0;
        let aux = false;

        for (let i = 1; cpf.length > i; i++) {
            if (cpf[i - 1] !== cpf[i]) {
                aux = true;
            }
        }

        if (aux === false) {
            return false;
        }

        for (let i = 0, p = 10; cpf.length - 2 > i; i++, p--) {
            v1 += cpf[i] * p;
        }

        v1 = (v1 * 10) % 11;

        if (v1 === 10) {
            v1 = 0;
        }

        if (v1 !== parseInt(cpf[9], 10)) {
            return false;
        }

        for (let i = 0, p = 11; cpf.length - 1 > i; i++, p--) {
            v2 += cpf[i] * p;
        }

        v2 = (v2 * 10) % 11;

        if (v2 === 10) {
            v2 = 0;
        }

        if (v2 !== parseInt(cpf[10], 10)) {
            return false;
        }
        return true;
    }

    function validate_cnpj(cnpj) {
        let v1 = 0;
        let v2 = 0;
        let aux = false;

        for (let i = 1; cnpj.length > i; i++) {
            if (cnpj[i - 1] !== cnpj[i]) {
                aux = true;
            }
        }

        if (aux === false) {
            return false;
        }

        for (let i = 0, p1 = 5, p2 = 13; cnpj.length - 2 > i; i++, p1--, p2--) {
            if (p1 >= 2) {
                v1 += cnpj[i] * p1;
            } else {
                v1 += cnpj[i] * p2;
            }
        }

        v1 %= 11;

        if (v1 < 2) {
            v1 = 0;
        } else {
            v1 = 11 - v1;
        }

        if (v1 !== parseInt(cnpj[12], 10)) {
            return false;
        }

        for (let i = 0, p1 = 6, p2 = 14; cnpj.length - 1 > i; i++, p1--, p2--) {
            if (p1 >= 2) {
                v2 += cnpj[i] * p1;
            } else {
                v2 += cnpj[i] * p2;
            }
        }

        v2 %= 11;

        if (v2 < 2) {
            v2 = 0;
        } else {
            v2 = 11 - v2;
        }

        if (v2 !== parseInt(cnpj[13], 10)) {
            return false;
        }
        return true;
    }

    function validate_cnpj_cpf(value) {
        var cnpj_cpf = value;

        cnpj_cpf = cnpj_cpf.trim();
        cnpj_cpf = cnpj_cpf.replace(/\./g, "");
        cnpj_cpf = cnpj_cpf.replace("-", "");
        cnpj_cpf = cnpj_cpf.replace("/", "");
        cnpj_cpf = cnpj_cpf.split("");

        if (cnpj_cpf.length === 11) {
            return validate_cpf(cnpj_cpf);
        } else if (cnpj_cpf.length === 14) {
            return validate_cnpj(cnpj_cpf);
        }
        return cnpj_cpf.length === 0;
    }

    return {
        validate_cnpj_cpf: validate_cnpj_cpf,
    };
});

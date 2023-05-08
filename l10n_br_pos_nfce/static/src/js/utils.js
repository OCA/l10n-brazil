odoo.define("l10n_br_pos_nfce.utils", function (require) {
    const ESTADOS_IBGE = {
        11: ["RO", "Rondônia"],
        12: ["AC", "Acre"],
        13: ["AM", "Amazonas"],
        14: ["RR", "Roraima"],
        15: ["PA", "Pará"],
        16: ["AP", "Amapá"],
        17: ["TO", "Tocantins"],
        21: ["MA", "Maranhão"],
        22: ["PI", "Piauí"],
        23: ["CE", "Ceará"],
        24: ["RN", "Rio Grande do Norte"],
        25: ["PB", "Paraíba"],
        26: ["PE", "Pernambuco"],
        27: ["AL", "Alagoas"],
        28: ["SE", "Sergipe"],
        29: ["BA", "Bahia"],
        31: ["MG", "Minas Gerais"],
        32: ["ES", "Espírito Santo"],
        33: ["RJ", "Rio de Janeiro"],
        35: ["SP", "São Paulo"],
        41: ["PR", "Paraná"],
        42: ["SC", "Santa Catarina"],
        43: ["RS", "Rio Grande do Sul"],
        50: ["MS", "Mato Grosso do Sul"],
        51: ["MT", "Mato Grosso"],
        52: ["GO", "Goiás"],
        53: ["DF", "Distrito Federal"],
    };

    const EDOC_PREFIXO = {
        55: "NFe",
        65: "NFCE",
    };

    function modulo11(base) {
        const pesos = "23456789".repeat(Math.floor(base.length / 8) + 1);
        const acumulado = base
            .split("")
            .reverse()
            .map((a, i) => parseInt(a) * parseInt(pesos[i]))
            .reduce((acc, val) => acc + val, 0);
        const digito = 11 - (acumulado % 11);
        return digito >= 10 ? 0 : digito;
    }

    class ChaveEdoc {
        static CUF = [0, 2]; // eslint-disable-line
        static AAMM = [2, 6]; // eslint-disable-line
        static CNPJ_CPF = [6, 20]; // eslint-disable-line
        static MODELO = [20, 22]; // eslint-disable-line
        static SERIE = [22, 25]; // eslint-disable-line
        static NUMERO = [25, 34]; // eslint-disable-line
        static FORMA = [34, 35]; // eslint-disable-line
        static CODIGO = [35, 43]; // eslint-disable-line
        static DV = [43]; // eslint-disable-line

        constructor(
            chave = false,
            codigoUF = false,
            anoMes = false,
            cnpjCpfEmitente = false,
            modeloDocumento = false,
            numeroSerie = false,
            numeroDocumento = false,
            formaEmissao = 1,
            codigoAleatorio = false,
            validar = false
        ) {
            if (!chave) {
                if (
                    !(
                        codigoUF &&
                        anoMes &&
                        cnpjCpfEmitente &&
                        modeloDocumento &&
                        numeroSerie &&
                        numeroDocumento
                    )
                ) {
                    throw new Error(
                        "ChaveEdoc: Parâmetros insuficientes para gerar chave"
                    );
                }

                let campos = codigoUF.toString().padStart(2, "0");
                campos += anoMes.toString();
                campos += cnpjCpfEmitente
                    .toString()
                    .replace(/^\d]/g, "")
                    .padStart(14, "0");
                campos += modeloDocumento.toString().padStart(2, "0");
                campos += numeroSerie.toString().padStart(3, "0");
                campos += numeroDocumento.toString().padStart(9, "0");
                campos += formaEmissao.toString().padStart(1, "0");

                if (!codigoAleatorio) {
                    codigoAleatorio = this.calculoCodigoAleatorio(campos);
                }

                campos += codigoAleatorio.toString().padStart(8, "0");
                campos += modulo11(campos).toString();

                this.modeloDocumento = parseInt(campos.substring(...ChaveEdoc.MODELO));
                this.prefixo = EDOC_PREFIXO[this.modeloDocumento] || "";
                this.chaveGerada = campos;

                if (validar) {
                    this.validar();
                }
            } else {
                const regex = /^\d{44}$/;
                const match = regex.exec(chave);
                if (!match) {
                    throw new Error("ChaveEdoc: Chave inválida");
                }
            }
        }

        calculoCodigoAleatorio(campos) {
            let soma = 0;
            for (let i = 0; i < campos.length; i++) {
                soma += parseInt(campos[i]) ** (3 ** 2);
            }

            const TAMANHO_CODIGO =
                ChaveEdoc.CODIGO[ChaveEdoc.CODIGO.length - 1] - ChaveEdoc.CODIGO[0];

            let codigo = soma.toString();
            if (codigo.length > TAMANHO_CODIGO) {
                codigo = codigo.slice(-TAMANHO_CODIGO);
            } else {
                codigo = codigo.padStart(TAMANHO_CODIGO, "0");
            }

            this._codigoAleatorio = codigo;

            return codigo;
        }

        validar() {
            return true;
        }

        get generatedChave() {
            return this._generatedChave;
        }

        set chaveGerada(textChave) {
            this._generatedChave = textChave;
        }

        get codigoAleatorio() {
            return this._codigoAleatorio;
        }
    }

    return {ChaveEdoc, ESTADOS_IBGE};
});

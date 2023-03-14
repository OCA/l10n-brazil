(function($) {
    $.extend(true, $.fn.dataTable.defaults, {
        info: false,
        scrollY: 160,
        dom: "frtip",
        scrollCollapse: true,
        language: {
            "emptyTable": "Nenhum registro encontrado",
            "zeroRecords": "Nenhum registro encontrado",
            "loadingRecords": "Carregando...",
            "processing": "Carregando...",
            "search": "Pesquisar",
            "paginate": {
                "next": "Próximo",
                "previous": "Anterior",
                "first": "Primeiro",
                "last": "Último"
            },
            "decimal": ",",
            "searchPlaceholder": "Buscar produto"
        } 
    });
}(jQuery));
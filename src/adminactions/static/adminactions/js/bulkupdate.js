"use strict";
(function ($) {
    $(function () {
        var model = $("meta[name='opts.label']").attr("content");
        var formData = $("form#bulk-update").serializeArray();
        $("#bulk-update").on("submit", function () {
            localStorage.setItem(model, JSON.stringify(formData));
        });
        $("#sel-cmd").on("change", function (e) {
            var selectedValue = this.value;
            if (this.value === "clear") {
                $(".col_field input").val("");
                $("#sel-cmd").val("");
            } else if (this.value === "saved") {
                var data = localStorage.getItem(model);
                if (data) {
                    $.each(formData, function (i, pair) {
                        $("input[name='" +  pair.name + "']").val(pair.value);
                        // $("td.col_field.field-" + pair.name + "-value input").val(pair.value);
                    });
                }
                $("#sel-cmd").val("");
            } else if (this.value === "default") {
                $('td.col_field').each(function () {
                    $(this).find('input').val($(this).data('col'))
                });
                $("#sel-cmd").val("");

            }
        })

        // console.log(formData);
    });
})(jQuery);

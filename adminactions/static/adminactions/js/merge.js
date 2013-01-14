(function ($) {
    $(function () {
        var select = function (from, to, val) {
            return function () {
                var $row = $(this).parent().parent();
                var $sel = $row.find(from);
                var $other = $row.find(to);
                var value = $sel.text();
                $sel.addClass("selected");
                $other.removeClass("selected");

                $row.find("input").val(val);
                $row.find(".selection").text(value);
            }
        }
        $('.from-first').click(select("td.first", "td.second", 1));
        $('.from-second').click(select("td.second", "td.first", 2));

//        $('.from-first').click(function () {
//                var $row = $(this).parent().parent();
//                var $sel = $row.find("td.first");
//                var $other = $row.find("td.second");
//                var value = $sel.text();
//                $sel.addClass("selected");
//                $other.removeClass("selected");
//
//                $row.find("input").val(1);
//                $row.find(".selection").text(value);
//        });

//        $('.from-second').click(function () {
//            var $row = $(this).parent().parent();
//            var value = $row.find("td.second").text();
//            $row.find("input").val(2);
//            $row.find(".selection").text(value);
//        });

    });
})(django.jQuery);

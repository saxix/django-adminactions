(function ($) {
    $(function () {
        var select = function (from, to, $val) {
            return function () {
                var $row = $(this).parent().parent();
                var $sel = $row.find(from);
                var $other = $row.find(to);
                var value = $sel.text();
                $sel.addClass("selected");
                $other.removeClass("selected");


                $row.find("input").val($val.val());

                $row.find(".selection").text(value);
            }
        }
        $('.origin').click(select("td.origin", "td.other", $('input[name="master-pk"]')));
        $('.other').click(select("td.other", "td.origin", $('input[name="other-pk"]')));

        $('a.swap').click(function(){
            var left = new Array();
            var right = new Array();

            $('.column.origin').each(function(){
                $(this).removeClass("selected");
                left.push($(this).text());
            });

            $('.column.other').each(function(){
                $(this).removeClass("selected");
                right.push($(this).text());
            });

            left.push($('input[name="master-pk"]').val());
            right.push($('input[name="other-pk"]').val());
            $('input[name="master-pk"]').val(right.pop());
            $('input[name="other-pk"]').val(left.pop());

            $($('.column.origin').get().reverse()).each(function(){
                $(this).text(right.pop());
            });
            $($('.column.other').get().reverse()).each(function(){
                $(this).text(left.pop());
            });

            $('.mergetable tr').each(function(){
                var value = $(this).find('input.result').val();
                if (value ==  $('input[name="master-pk"]').val()){
                    $(this).find('td.origin').addClass("selected");
                }
                if (value ==  $('input[name="other-pk"]').val()){
                    $(this).find('td.other').addClass("selected");
                }

            });

        });
    });
})(django.jQuery);

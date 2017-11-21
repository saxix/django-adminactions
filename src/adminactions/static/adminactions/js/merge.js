(function ($) {
    $(function () {
        var select = function (from) {
            return function ( event ) {
                event.preventDefault();
                var $row = $(this).parent().parent();
                var $sel = $row.find(from);
                $('.result input', $row).val($('input.raw-value', $sel).val());
                highlight();
            };
        };
        var highlight = function () {
            var RIGHT = [];
            $('.mergetable tr.merge-row').each(function () {

                var $result = $(this).find('td.result');
                var $left = $(this).find('td.origin');
                var $right = $(this).find('td.other');
                var field_name = $(this).find('td:first').attr('data-content');


                $('td', this).removeClass("selected");

                if ($('input.raw-value', $result).val() === $('input.raw-value', $left).val()) {
                    $(this).find('td.origin').addClass("selected");
                    $('p.display', $result).text($('p.display', $left).text());
                } else if ($('input.raw-value', $result).val() === $('input.raw-value', $right).val()) {
                    $(this).find('td.other').addClass("selected");
                    $('p.display', $result).text($('p.display', $right).text());
                    RIGHT.push(field_name);
                }else if ($('.original .display', this).text() !== $('.result .display', this).text()){
                    $(this).addClass("changed");
                }
            });
            $('.merge-form input[name=field_names]').val(RIGHT);
        };

        $('a.origin').click(select("td.origin"));
        $('a.other').click(select("td.other"));

        $('a.swap').click(function ( event ) {
            event.preventDefault();
            var left = [];
            var right = [];
            var $master = $('input[name="master_pk"]');
            var $other = $('input[name="other_pk"]');

            $('.column.origin').each(function () {
                left.push([$('input.raw-value', this).val(), $('.display', this).text()]);
            });

            $('.column.other').each(function () {
                right.push([$('input.raw-value', this).val(), $('.display', this).text()]);
            });

            left.push($master.val());
            right.push($other.val());

            $master.val(right.pop());
            $other.val(left.pop());

            $('span[id="master_pk"]').text($master.val());
            $('span[id="other_pk"]').text($other.val());

            $($('.column.origin').get().reverse()).each(function () {
                var entry = right.pop();
                $('input.raw-value', this).val(entry[0]);
                $('.display', this).text(entry[1]);
            });
            $($('.column.other').get().reverse()).each(function () {
                var entry = left.pop();
                $('input.raw-value', this).val(entry[0]);
                $('.display', this).text(entry[1]);
            });
            highlight();
        });

        highlight();

    });
})(django.jQuery);

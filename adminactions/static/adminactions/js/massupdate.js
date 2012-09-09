(function($) {
$(function() {
    $('.col_field input, .col_field select').each(function() {
        if (!$(this).parent().parent().find('.col_enabler input[type=checkbox]').is(':checked')){
            $(this).attr('disabled', 'disabled');
        }
    });
    $('.fastfieldvalue').click(function() {
        var check = $(this).parent().parent().find('.enabler');
        var selection = $(this).text();
        $(check).attr('checked', true);
        var target = $(this).parent().parent().find('input, select').not('.enabler');
        $(target).removeAttr('disabled');
        if ($(target).is('select')) {
            $('option', target).each(function(i, selected) {
                if ($(this).text() == selection) {
                    $(this).attr('selected', true);
                }
            });
        } else if ($(target).is('input[type=checkbox]')) {
            $(target).attr('checked', selection=='True');
        } else if ($(target).is('input')) {
            $(target).val(selection);
        }
    });
    $('.enabler').click(function() {
        var target = $(this).parent().parent().find('.col_field input, .col_field select');
        if ($(this).is(':checked')) {
            $(target).removeAttr('disabled');
        } else {
            $(target).attr('disabled', 'disabled');
        }
    })
});
})(django.jQuery);

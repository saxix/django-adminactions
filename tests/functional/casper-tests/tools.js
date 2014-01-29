/**
 *
 * User: sax
 * Date: 12/28/13
 * Time: 2:33 PM
 *
 */
module.exports = (function () {
    function assertStatusCode(response) {
        if (response == undefined || response.status >= 400) {
            console.log(response.status);
            casper.capture("ERROR.png");
            casper.test.assert(false);
        }
    }
    function selectElements(values){
        var ids = values.split(",");
        ids.forEach(function(entry){
            casper.click("[value='" +  entry +"']");
        });
    }

    function runAction(action_name, elements) {
        casper.fill('#changelist-form', {
            action: action_name
        }, true);

    }

    return {
        assertStatusCode: assertStatusCode,
        selectElements: selectElements,
        runAction: runAction,
    };
})();

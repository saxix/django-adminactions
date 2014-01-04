/**
 *
 * User: sax
 * Date: 12/27/13
 * Time: 8:02 PM
 *
 */

casper.test.comment('Casper merge test');
var helper = require('./djangocasper.js'),
    utils = require('utils'),
    http = require('http'),
    tools = require('./tools.js'),
    fs = require('fs');


helper.scenario(
    casper.cli.options['url'],
    function (response) {
        /*
         select records in changelist
         */
        tools.assertStatusCode(response);
        casper.test.assertTextExists('Select user to change');
        tools.selectElements(casper.cli.options['ids']);
        this.fill('#changelist-form', {action: 'merge'}, false);
        this.click('button[name="index"]');
        this.waitForSelector("#id_last_name",
            null,
            function () {
                casper.capture("pageError.png");
            });
    },
    function (response) {
        /* merge */
        tools.assertStatusCode(response);
        casper.test.assertTextExists('Master #' + casper.cli.options['master_id']);
        this.click('#other_last_name');
        this.click('#other_first_name');
        this.waitForSelector("td.column,other,selected");
        this.click('input[name=preview]');
        this.waitForSelector("table.mergetable",
            null,
            function () {
                casper.capture("pageError.png");
            });
    },
    function (response) {
         /* preview */
        casper.test.assertTextExists('After Merging',
            function () {
                casper.capture("pageError.png");
            });
        this.click('input[name=apply]');
        this.waitForSelector("#changelist-form",
            null,
            function () {
                casper.capture("pageError.png");
            });
    },
    function (response) {
        this.test.assert(true);
    }
);


helper.run();


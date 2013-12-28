/**
 *
 * User: sax
 * Date: 12/27/13
 * Time: 8:02 PM
 *
 */

casper.test.comment('Casper mass update test');
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
        this.fill('#changelist-form', {action: 'mass_update'}, false);
        this.click('button[name="index"]');
        this.waitForSelector("#id_last_name",
            null,
            function () {
                casper.capture("pageError.png");
            });
    },
    function (response) {
        tools.assertStatusCode(response);
        this.click('input[name="chk_id_first_name"]');
        this.click('input[name="chk_id_last_name"]');
        this.sendKeys('#id_first_name', casper.cli.options['first_name']);
        this.sendKeys('#id_last_name', casper.cli.options['last_name']);

        this.click('input[type="submit"]');
        this.waitForSelector("#changelist-form",
            null,
            function () {
                casper.capture("pageError.png");
            });
    },
    function (response) {
        casper.test.assertTextExists(casper.cli.options['last_name']);
    },
    function (response) {
        this.test.assert(true);
    }
);

helper.run();


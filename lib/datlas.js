/*
 * datlas
 * https://github.com/vxtindia/datlas
 *
 * Copyright (c) 2013 Debjeet Biswas
 * Licensed under the MIT license.
 */

'use strict';

var exec = require('child_process').exec,
    fs = require('fs');

exports.getData = function(userAgent, cb) {
  if (!cb) throw new Error('Callback required');
  if (!userAgent) return cb(new Error('Invalid user agent string'));

  exec('python getDeviceData.py -ua "' + userAgent + '"', {cwd: __dirname}, function(err, stdout, stderr) {
    if (err) return cb(new Error(err));
    if (stderr) return cb(new Error(stderr));

    cb(null, JSON.parse(stdout));
  });

};

exports.init = function(key) {
  var file = __dirname + '/DeviceAtlasCloud/Client.py';
  if (!key || !fs.existsSync(file)) return;

  fs.readFile(file, 'utf8', function(err, data) {
    if (err) return console.error(err);

    fs.writeFileSync(file, data.replace(/self.LICENSE_KEY =.*/g, "self.LICENSE_KEY = '" + key + "'"));
  });
};


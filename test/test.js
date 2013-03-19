var da = require('../lib/datlas');

da.init('0b9dfdfe72dd2f40db02c002946ce0d0');
da.getData('Mozilla/5.0 (iPhone; CPU iPhone OS 5_0 like Mac OS X) AppleWebKit/534.46 (KHTML, like Gecko) Version/5.1 Mobile/9A334 Safari/7534.48.3', function(err, result) {
  if (err) return console.error(err);
  console.log(result);
});

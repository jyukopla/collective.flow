define([
  'jquery',
  'pat-base',
], function($, Base) {
  'use strict';

  return Base.extend({
    name: 'folding-fieldsets',
    trigger: '.pat-folding-fieldsets',

    init: function($el) {
      $el.find('fieldset > legend').each(function() {
        var $legend = $(this).contents().wrap('<a href="#"></a>').parent();
        var $fields = $(this).siblings()
          .wrap('<div id="' + $legend.attr('id') + '-fields"></div>').parent();

        $legend.attr('aria-controls', $fields.attr('id'));
        $legend.attr('aria-expanded', 'true');
        $fields.attr('aria-hidden', 'false');

        var toggle = function(e) {
          e.preventDefault();
          if ($legend.attr('aria-expanded') === 'true') {
            $fields.hide();
            $fields.attr('aria-hidden', 'true');
            $legend.attr('aria-expanded', 'false');
          } else {
            $fields.show();
            $fields.attr('aria-hidden', 'false');
            $legend.attr('aria-expanded', 'true');
          }
        };

        $legend.on('click', toggle);
        if ($fields.find('.error').length === 0) {
          $legend.click();
        }

        // a11y
        $legend.on('keyup', function(e) {});
        $legend.on('keydown', function(e) {
          if (e.keyCode === 27) {
            toggle.apply(this, [e]);
          }
        });
      });

      if ($el.find('.error').length === 0) {
        $el.find('fieldset:first > legend a').each(function() {
          $(this).click();
        });
      }
    }
  });
});

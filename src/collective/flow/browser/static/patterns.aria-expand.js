define([
  'jquery',
  'pat-base',
  'pat-logger'
], function($, Base, logger) {
  'use strict';

  var enabled = false;

  return Base.extend({
    name: 'aria-expand',
    trigger: '.pat-aria-expand',

    init: function($el) {
      var log = logger.getLogger('aria-expand');

      var settings = {
        event: 'click',
        delay: 0,
        hidden: true,
        transition: 'aria-expand-transition',
        toggle: null,
        focus: null
      };

      var $target;
      var $toggleTarget = '';
      var toggleClass = '';
      var $focusTarget = '';

      if (!$el.attr('aria-controls')) {
        log.error('No attribute "aria-controls" defined for "' +
          $el.prop('outerHTML') + '".');
        return;
      }

      if ($el.attr('aria-controls')) {
        $target = $('#' + $el.attr('aria-controls'));
      } else {
        $target = $el;
      }

      if (!$target || $target.length === 0) {
        log.error('No target found for "#' +
          $el.attr('aria-controls') + '".');
        return;
      }

      if (settings.toggle) {
        var index = settings.toggle.lastIndexOf('.');
        if (index > -1) {
          $toggleTarget = $(settings.toggle.slice(0, index));
          toggleClass = settings.toggle.slice(index + 1);
          if ($toggleTarget.length === 0) {
            log.warn('Toggle target "' +
              settings.toggle.slice(0, index) + '" not found.');
          }
          if (toggleClass.length === 0) {
            log.warn('Invalid toggle setting "' +
              settings.toggle + '".');
          }
        } else {
          log.warn('Invalid toggle setting "' +
            settings.toggle + '".');
        }
      }

      if (settings.focus) {
        $focusTarget = $(settings.focus);
        if ($focusTarget.length === 0) {
          log.warn('Focus target "' +
            settings.focus + '" not found.');
        }
      }

      var hidden = false;
      var timeout = null;

      $el.on('aria-expand-hide', function() {
        clearTimeout(timeout);
        timeout = null;
        $el.attr('aria-expanded', 'false');
        $el.removeClass(settings.transition);
        $target.attr('aria-hidden', 'true');
        if (settings.hidden) { $target.attr('hidden', ''); }
        if ($toggleTarget.length && toggleClass.length) {
          $toggleTarget.removeClass(toggleClass);
        }
        $target.removeClass(settings.transition);
        hidden = true;
      });

      $el.on('aria-expand-show', function() {
        clearTimeout(timeout);
        timeout = null;
        $el.attr('aria-expanded', 'true');
        $el.removeClass(settings.transition);
        $target.attr('aria-hidden', 'false');
        $target.removeAttr('hidden');
        if ($toggleTarget.length && toggleClass.length) {
          $toggleTarget.addClass(toggleClass);
        }
        if ($focusTarget.length) {
          $focusTarget.focus();
        }
        $target.removeClass(settings.transition);
        hidden = false;
      });

      if ($el.attr('aria-expanded') === 'true' ||
        $target.attr('aria-hidden') !== 'true') {
        $el.trigger('aria-expand-show');
      } else {
        $el.trigger('aria-expand-hide');
      }

      function toggle() {
        if (hidden) {
          $el.trigger('aria-expand-show');
        } else {
          $el.trigger('aria-expand-hide');
        }
      }

      $el.on(settings.event, function(e) {
        if (timeout !== null) { toggle(); }
        $el.addClass(settings.transition);
        $target.addClass(settings.transition);
        $target.removeAttr('hidden');
        timeout = setTimeout(toggle, settings.delay);
        e.stopPropagation();
        e.preventDefault();
      });

      // a11y
      $el.on('keyup', function(e) {});

      if (enabled === false) {
        $(window).on('keydown', function(e) {
          if (e.keyCode === 27) {
            var original = e.originalEvent || null;
            var target = original ? original.target : null;
            if (original && target && $(target).parents('form').length === 0) {
              $('[aria-expanded="true"].pat-aria-expand')
                .trigger(settings.event);
            }
          }
          return true;
        });
        enabled = true;
      }
    }
  });
});

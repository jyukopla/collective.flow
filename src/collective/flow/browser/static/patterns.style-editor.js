define([
  'jquery',
  'pat-base',
  'ace'
], function($, Base) {
  'use strict';

  return Base.extend({
    name: 'style-editor',
    trigger: '.pat-style-editor',

    init: function($el) {
      var self = this;
      if (!window.ace){
        setTimeout(function() { self.init(); }, 200);
        return;
      }
      var ace = window.ace;

      ace.config.set("packaged", true);
      ace.config.set("basePath", "++plone++static/components/ace-builds/src/");

      var editDiv = $('<div>', {
        position: 'relative',
        width: '100%',
        height: $el.height(),
        'class': $el.attr('class')
      }).insertBefore($el);

      $el.hide();

      var editor = ace.edit(editDiv[0]);
      window.foo = editor;

      editor.setShowPrintMargin(false);
      editor.$blockScrolling = Infinity;
      editor.renderer.setShowGutter(true);
      editor.getSession().setMode("ace/mode/css");
      editor.getSession().setTabSize(2);
      editor.getSession().setUseSoftTabs(true);
      editor.getSession().setUseWrapMode(true);
      editor.getSession().setValue($el.val());

      editor.on('blur', function() {
        $el.val(editor.getSession().getValue());
      });
    }
  });
});

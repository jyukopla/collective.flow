/******************************************************************************
 *
 * jQuery functions for the plone.app.discussion comment viewlet and form.
 *
 ******************************************************************************/
/* global require */

if(require === undefined) {
  require = function(reqs, torun) {  // jshint ignore:line
  'use strict';
    return torun(window.jQuery);
  };
}

require([  // jshint ignore:line
  'jquery'
], function ($) {
  'use strict';

  // This unnamed function allows us to use $ inside of a block of code
  // without permanently overwriting $.
  // http://docs.jquery.com/Using_jQuery_with_Other_Libraries

  /**************************************************************************
   * Create a reply-to-comment form right beneath the form that is passed to
   * the function. We do this by copying the regular comment form and
   * adding a hidden in_reply_to field to the form.
   **************************************************************************/
  $.createReplyForm = function (el) {
    var id = el.attr('id');
    var reply_button = el.find('.reply-to-comment-button')
      .css('display', 'none');

    // Clone the global reply div at the end of the page template that contains
    // the regular comment form.
    var reply_div = $('#commenting').clone(true);

    // Fetch the reply form inside the reply div
    var reply_form = reply_div.find('form');

    // Remove the ReCaptcha JS code before appending the form. If not
    // removed, this causes problems
    reply_div.find('#formfield-form-widgets-captcha')
      .find('script')
      .remove();

    // Insert the cloned comment form right after the reply button of the
    // current comment.
    reply_button.after(reply_div);

    // Change the id of the textarea of the reply form to avoid conflicts
    reply_form.find('#formfield-form-widgets-comment-text')
      .attr('id', 'formfield-form-widgets-new-textarea' + id);
    reply_form.find('#form-widgets-comment-text')
      .attr('id', 'form-widgets-new-textarea' + id);

    // Populate the hidden 'in_reply_to' field with the correct comment id
    reply_form.find('input[name="form.widgets.in_reply_to"]')
      .val(id);

    /**********************************************************************
     * If the user hits the 'clear' button of an open reply-to-comment form,
     * remove the form and show the 'reply' button again.
     **********************************************************************/
    reply_div.find('input[name="form.buttons.cancel"]').click(function (e) {
      e.preventDefault();

      /* Find the reply-to-comment form and hide and remove it again. */
      reply_button.next().remove();

      /* Show the reply-to-comment button again. */
      reply_button.css('display', 'inline');
    });

    /* Show the cancel button */
    reply_form.find('input[name="form.buttons.cancel"]')
      .css('display', 'inline');
  };

  /**************************************************************************
   * Remove all error messages and field values from the form that is passed
   * to the function.
   **************************************************************************/
  $.clearForm = function (form_div) {
    form_div.find('.error').removeClass('error');
    form_div.find('.fieldErrorBox').remove();
    form_div.find('input[type="text"]').val('');
    form_div.find('textarea').val('');
    /* XXX: Clean all additional form extender fields. */
    form_div.find('[aria-expanded="true"]').click();
  };

  var init; init = function ($el) {

    /**********************************************************************
     * If the user hits the 'reply' button of an existing comment, create a
     * reply form right beneath this comment.
     **********************************************************************/
    $el.find('.reply-to-comment-button').bind('click', function (e) {
      var comment_div = $(this).parents().filter('.comment');
      $.createReplyForm(comment_div);
      $.clearForm(comment_div);
    });

    /**********************************************************************
     * Publish a single comment.
     **********************************************************************/
    $el.find('input[name="form.button.PublishComment"]').on('click', function () {
      var trigger = this;
      var form = $(this).parents('form');
      var data = $(form).serialize() + '&ajax_load=1';
      var form_url = $(form).attr('action');
      $.ajax({
        type: 'GET',
        url: form_url,
        data: data,
        context: trigger,
        success: function (msg) {  // jshint ignore:line
          // remove button (trigger object can't be directly removed)
          form.find('input[name="form.button.PublishComment"]').remove();
          form.parents('.state-new').toggleClass('state-new').toggleClass('state-acknowledged');
          form.parents('.state-pending').toggleClass('state-pending').toggleClass('state-published');
        },
        error: function (msg) {  // jshint ignore:line
          return true;
        }
      });
      return false;
    });

    /**********************************************************************
     * Edit a comment
     **********************************************************************/
    if ($.fn.prepOverlay) {
      $el.find('form[name="edit"]').prepOverlay({
        cssclass: 'overlay-edit-comment',
        width: '60%',
        subtype: 'ajax',
        filter: '#content>*'
      });
    }

    /**********************************************************************
     * Submit a comment
     **********************************************************************/
    $el.find('input[name$=".buttons.comment"]').on('click', function (e) {
      e.preventDefault();
      var $trigger = $(this);
      var $form = $trigger.parents('form');
      var data = $form.serialize();  //  + '&ajax_load=1';
      var form_url = $form.attr('action');
      data += '&' + $trigger.attr('name') + '=' + $trigger.val();
      $trigger.attr('disabled', 'disabled');
      $.ajax({
        type: 'POST',
        url: form_url,
        data: data,
        context: $trigger,
        success: function (data) {  // jshint ignore:line
          var $old, $new;
          if ($trigger.parents('.reply').length) {
            $old = $trigger.parents('.reply').prev('.discussion');
            $new = $(data)
              .find('#' + $trigger.attr('id'))
              .parents('.reply').prev('.discussion');
            if ($old.length && $new.length) {
              $old.replaceWith($new);
              init($new);
            } else if ($new.length) {
              $trigger.parents('.reply').before($new);
              init($new);
            }
          } else {
            $old = $trigger.parents('.discussion');
            $new = $(data)
              .find('#' + $trigger.parents('.comment').attr('id'))
              .parents('.discussion');
            if ($old.length && $new.length) {
              $old.replaceWith($new);
              init($new);
            }
          }
          $trigger.attr('disabled', null);
          $.clearForm($trigger.parents('.comment, .reply, .discussion'));
        },
        error: function (req, error) {  // jshint ignore:line
          $trigger.attr('disabled', null);
          return true;
        }
      });
      return false;
    });

    /**********************************************************************
     * Delete a comment and its answers.
     **********************************************************************/
    $el.find('input[name="form.button.DeleteComment"]').on('click', function () {
      var trigger = this;
      var form = $(this).parents('form');
      var data = $(form).serialize();
      var form_url = $(form).attr('action');
      $.ajax({
        type: 'POST',
        url: form_url,
        data: data,
        context: $(trigger).parents('.comment'),
        success: function (data) {  // jshint ignore:line
          var comment = $(this);
          var clss = comment.attr('class');
          // remove replies
          var treelevel = parseInt(clss[clss.indexOf('replyTreeLevel') + 'replyTreeLevel'.length], 10);
          // selector for all the following elements of lower level
          var selector = '.replyTreeLevel' + treelevel;
          for (var i = 0; i < treelevel; i++) {
            selector += ', .replyTreeLevel' + i;
          }
          comment.nextUntil(selector).each(function () {
            $(this).fadeOut('fast', function () {
              $(this).remove();
            });
          });
          // Add delete button to the parent
          var parent = comment.prev('[class*="replyTreeLevel' + (treelevel - 1) + '"]');
          parent.find('form[name="delete"]').css('display', 'inline');
          // remove comment
          $(this).fadeOut('fast', function () {
            $(this).remove();
          });
        },
        error: function (req, error) {  // jshint ignore:line
          return true;
        }
      });
      return false;
    });

    $el.find('input[name$=".buttons.cancel"]').click(function (e) {
      e.preventDefault();
      $.clearForm($(this).parents().filter('.reply'));
    });

    /**********************************************************************
     * By default, hide the reply and the cancel button for the regular add
     * comment form.
     **********************************************************************/
    $el.find('.reply').find('input[name="form.buttons.reply"]')
      .css('display', 'none');
    $el.find('.reply').find('input[name="form.buttons.cancel"]')
      .css('display', 'none');


    /**********************************************************************
     * By default, show the reply button only when Javascript is enabled.
     * Otherwise hide it, since the reply functions only work with JS
     * enabled.
     **********************************************************************/
    $el.find('.reply-to-comment-button').removeClass('hide');

  };

  /**************************************************************************
   * Window Load Function: Executes when complete page is fully loaded,
   * including all frames,
   **************************************************************************/
  $(window).load(function () {

    /**********************************************************************
    * If the user has hit the reply button of a reply-to-comment form
    * (form was submitted with a value for the 'in_reply_to' field in the
    * request), create a reply-to-comment form right under this comment.
    **********************************************************************/
    var in_reply_to_field =
        $('#commenting input[name="form.widgets.in_reply_to"]');
    if (in_reply_to_field.length !== 0 && in_reply_to_field.val() !== '') {
        var current_reply_id = '#' + in_reply_to_field.val();
        var current_reply_to_div = $('.discussion').find(current_reply_id);
        $.createReplyForm(current_reply_to_div);
        $.clearForm($('#commenting'));
    }

    init($('#commenting, .discussion, .reply'));
  });

});

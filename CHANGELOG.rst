Changelog
=========

1.3.6 (unreleased)
------------------

- Add edit form cancel button with behavior
  [Asko Soukka]

- Change edit form save and workflow action buttons to depend on behavior
  [Asko Soukka]

1.3.5 (2018-11-12)
------------------

- Fix to clear locks when saving with worklflow action fix issue where lock
  prevented workflow action
  [Asko Soukka]

1.3.4 (2018-10-31)
------------------

- Fix issue where form:validator -validators were not serialized from schema
  [Asko Soukka]

1.3.3 (2018-10-29)
------------------

- Fix issue where default values were saved for fields with defaultFactories
  [Asko Soukka]

1.3.2 (2018-10-24)
------------------

- Tweak metromap to include exceptional states not in the heuristic happy path
  [Asko Soukka]

1.3.1 (2018-10-24)
------------------

- Update flow folder listing heading
  [Asko Soukka]

1.3.0 (2018-10-24)
------------------

- Implement submission_transition and attachment_transition
  [Asko Soukka]
- Add default value burning behavior to also set static default values
  [Asko Soukka]

1.2.0 (2018-10-22)
------------------

- Tweak metromap heuristics to better skip reopen transitions when seeking for
  the next state
  [Asko Soukka]
- Make flow folder customizable fields configurable in schema per field
  [Asko Soukka]
- Change language negotiation to use the language of the closest navigation
  root as the default language
  [Asko Soukka]
- Fix issue where language specific schema was create for default language
  [Asko Soukka]
- Fix issue where action urls were broken on schema context
  [Asko Soukka]
- Fix issue where default language (en-us) did not match negotiated language (en)
  [Asko Soukka]

1.1.3 (2018-09-24)
------------------

- Fix parents helper to be usable without iface filter
  [Asko Soukka]
- Fix issue where AjaxSelectWidget dislay mode broke keywords widget
  [Asko Soukka]

1.1.2 (2018-09-19)
------------------

- Change to use _v_volatile caching for field history and disable history on
  POSTs to mitigate with CMFEditions' conflict errors
  [Asko Soukka]

1.1.1 (2018-09-11)
------------------

- Fix issue where comments were not shown
  [Asko Soukka]

1.1.0 (2018-09-10)
------------------

- Implement Plone REST API expansion
  [Asko Soukka]
- Change to only show comment option for fields with values
  [Asko Soukka]

1.0.3 (2018-09-10)
------------------

- Fix to better catch CMFEditions history lookup ConflictErrors
  [Asko Soukka]

1.0.2 (2018-09-07)
------------------

- Fix issue where inline_validation calls failed when validation got errors
  from TTW validators
  [Asko Soukka]
- Fix issues where date picker and ajax select widgets were not usable without
  javascript
  [Asko Soukka]

1.0.1 (2018-09-04)
------------------

- Fix issue where CMFEditions raised ConflictError by skipping history view on
  those situations
  [Asko Soukka]
- Back to development: 1.0.1
  [Asko Soukka]

1.0.0 (2018-09-02)
------------------

- Fix issue where portal repository usage resulted in false CSRF-warning
  [Asko Soukka]
- Optimize to not render history or comments viewlets when
  collective.futures is awaiting to capture the request
  [Asko Soukka]
- Add impersonation, top buttons and bottom buttons submission behaviors
  [Asko Soukka]

0.9.0 (2018-08-29)
------------------

- Add listing for creator's own submissions for add form
  [Asko Soukka]
- Fix to render all edit buttons in dedicated viewlets to apply permissions
  properly
  [Asko Soukka]

0.8.5 (2018-08-27)
------------------

- Fix issue where views were rendered twice when adding or replying to comments
  [Asko Soukka]
- Fix issue where designer failed for forms without submission behaviors
  [Asko Soukka]
- Fix issue where choice field defaultFactory-values were not serialized from designer to xml
  [Asko Soukka]
- Fix where field settings failed when submission_behaviors was not set
  [Asko Soukka]

0.8.4 (2018-08-22)
------------------

- Simplify metromap and submission action buttons
  [Asko Soukka]
- Make the default fieldest heading visible on forms
  [Asko Soukka]
- Fix AjaxSelectWidget to show vocabulary titles on display mode
  [Asko Soukka]
- Distinct add new comment button from starting a discussion button
  [Asko Soukka]

0.8.3 (2018-08-21)
------------------

- Patch issue with ajax select widget converter failing with None values
  [Asko Soukka]

0.8.2 (2018-08-21)
------------------

- Fix issues with localizing template values for localized submission
  [Asko Soukka]

0.8.1 (2018-08-21)
------------------

- Fix issue where permission check for being able to impersonate failed
  [Asko Soukka]

0.8.0 (2018-08-21)
------------------

- Add submission value interpolation to resolve default values for empty fields
  [Asko Soukka]
- Fix issue where empty submission path resulted in saving submission to root
  flow folder
  [Asko Soukka]
- Add localization support for form configuration
  [Asko Soukka]
- Fix issue were schema specification description did fail when digest was
  still missing
  [Asko Soukka]
- Fix issue where 'force' save flag was not passed when applied save for schema
  groups
  [Asko Soukka]
- Fix issue where form submit button update did update shared class instead of
  form instance
  [Asko Soukka]
- Allow support for sub schema ajax vocabularies
  [Asko Soukka]
- Add built-in impersonation for add form
  [Asko Soukka]
- Implement per field toggle for comments and changelog
  [Asko Soukka]
- Add subheading into display form views
  [Asko Soukka]
- Implement behavior to fill missing values
  [Asko Soukka]
- Fix broken transition in flow workflow
  [Asko Soukka]

0.7.4 (2018-08-15)
------------------

- Add support for serializing default factories
  [Asko Soukka]

0.7.3 (2018-08-15)
------------------

- Add naive firstname and lastname default factories
  [Asko Soukka]
- Fix issue where failed to parse schema with broken default factory path
  [Asko Soukka]

0.7.1 (2018-08-14)
------------------

- Fix flow data descriptor schema order and cache descriptor in request
  [Asko Soukka]
- Fix regexp for matching translations
  [Asko Soukka]
- Fix state missing exit-transition in Flow Folder Workflow
  [Asko Soukka]

0.7.0 (2018-08-14)
------------------

- Add support for multilingual forms
  [Asko Soukka]
- Add custom "Flow" content menu
  [Asko Soukka]

0.6.1 (2018-07-06)
------------------

- Fix issue where flow filing template could not be empty
  [Asko Soukka]
- Fix issue where field permission checking was broken on add/submit form
  [Asko Soukka]
- Fix issue where flow folder still required at least one behavior to be added
  [Asko Soukka]

0.6.0 (2018-07-04)
------------------

- Fix CSS injection to allow CDATA
  [Asko Soukka]
- Add workflow buttons to display form
  [Asko Soukka]
- Add workflow buttons to edit form
  [Asko Soukka]
- Fix issue where folding fieldsets pattern did not properly wrap fields
  [Asko Soukka]
- Implement acknowledgement workflow for field comments
  [Asko Soukka]
- Add to cache submission dynamic interfaces by request
  [Asko Soukka]
- Fix submission behaviors not required
  [Asko Soukka]
- Add support (and patch Plone to support) for z3c form widget layouts
  [Asko Soukka]
- Add field level commenting behavior
  [Asko Soukka]
- Add field history behavior
  [Asko Soukka]
- Fix issue where editing submissions did not fire object events properly; Fix submissin update to use data managers
  [Asko Soukka]

0.5.0 (2018-06-20)
------------------

- Add re-usable supermodel compatible default value factories
  [Asko Soukka]

- Implement DX permission checker for flow schemas
  [Asko Soukka]

- Add support for submission behaviors
  [Asko Soukka]

- Add folding fieldsets; Add generic metromap; Add edit-button
  [Asko Soukka]

- Add customizable title and filing structure
  [Asko Soukka]

- Add form flow workflow
  [Asko Soukka]

- Fix issue where flow submission did not show all fieldsets
  [Asko Soukka]

- Add support for customized schema for add forms
  [Asko Soukka]

- Hide richtextlabel labels when viewing submission; show all fieldsets for
  submissions
  [Asko Soukka]

- Add display widget for richtextlabel
  [Asko Soukka]

- Change submission id to be its UUID
  [Asko Soukka]

- Fix issue where new submissions were misssing UUID
  [Asko Soukka]


0.4.2 (2018-04-18)
------------------

- Fix issue where submission thanks view showed default values for intentionally missing values
  [Asko Soukka]


0.4.1 (2018-04-18)
------------------

- Update default factories
  [Asko Soukka]

0.4.0 (2018-04-18)
------------------

- Add support for defaultFactory
  [Asko Soukka]
- Add custom validator
  [Asko Soukka]
- Add useful defaultFactories
  [Asko Soukka]

0.3.0 (2018-04-17)
------------------

- Restore customization of vocabularies when original vocabulary was empty
  [Asko Soukka]
- Fix regression caused by wrong import
  [Asko Soukka]
- Reimplement ACE editor integration as custom pattern
  [Asko Soukka]
- Fix issue where custom JavaScript was not renderd as CDATA
  [Asko Soukka]

0.2.4 (2018-04-11)
------------------

- Enable pat-texteditor
  [Asko Soukka]

0.2.3 (2018-03-22)
------------------

- Add support for default values for repeating items
  [Asko Soukka]

0.2.2 (2018-03-22)
------------------

- Update styles
  [Asko Soukka]

0.2.1 (2018-03-22)
------------------

- Fix issue with requirejs patch
  [Asko Soukka]

0.2.0 (2018-03-22)
------------------

- Change folder view to be folder listing when folder has sub folders
  [Asko Soukka]
- Disable customization of vocabulary values for now
  [Asko Soukka]
- Fix issue where CSS cache was not purged after folder was updated
  [Asko Soukka]
- Fix datagrid styles when submission has occurred
  [Asko Soukka]

0.1.2 (2018-03-15)
------------------

- Add three empty lines as default values for multi-line fields
  [datakurre]

0.1.1 (2018-03-15)
------------------

- Try to fix issue where schemaeditor JS did not work with webpack built JS
  [datakurre]
- Enable flow custom css and javascript
  [datakurre]
- Fix issue which prevented adding a new flow folder into an existing flow
  [datakurre]


0.1.0 (2018-02-28)
------------------

- Technology preview.

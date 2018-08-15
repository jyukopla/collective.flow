Changelog
=========

0.7.2 (unreleased)
------------------

- Nothing changed yet.


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

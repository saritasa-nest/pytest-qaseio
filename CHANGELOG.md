# Version history

We follow [Semantic Versions](https://semver.org/).

## Version 2.6.0 (24.07.25)

- Add pytest hook `pytest_get_run_name` and `--qase-run-name` option to
  specify qase.io run name or implement your own logic for it

  By default, `pytest_get_run_name` will set title from `--qase-run-name` or
  title generated by `RUN_NAME_TEMPLATE` (as before).

## Version 2.5.0 (18.07.25)

- Add pytest hook `pytest_get_debug_info` to override `DebugInfo`

  This allows customizing `DebugInfo` for failed tests in various testing
  frameworks. Previously it was based on selenium webdriver which is not
  compatible with other frameworks (e.g. `Playwright`)

  By default, `pytest_get_debug_info` will return `SeleniumDebugInfo`, as before.

- Make `selenium` dependency optional

  `pytest-qaseio` is not only used with Selenium-based tests, so we made
  `selenium` optional to avoid installing unused dependencies (in package it is
  only used for type annotations)

## Version 2.4.0

- Update ``xfailed`` tests handling:

  We decided to use ``blocked`` status so as not to mislead the QA team. If
  they see a failed case, they will go to retest it. But xfail implies that the
  case fails for some already known reason. So the blocked status will let them
  know that the case is blocked for some reason described in the xfail comment
  (this comment will be duplicated as a result of the case run).

## Version 2.3.0

- Fix skipping reports for already passed tests

## Version 2.2.0

- Replace `qaseio` to `qase-api-client` because first one was [deprecated](https://github.com/qase-tms/qase-python##deprecated)

## Version 2.1.2

- Update `DebugInfo.generate_debug_comment`: set default values for `screenshot_url`
  and `html_url`

## Version 2.1.1

- Improve exception handling in `DebugInfo`

## Version 2.1.0

- Update environment tools
- Update pyproject.toml for backward compatibility (freeze arrow on 1.2.3 version)

## Version 2.0.0

- Use updated `qaseio` sdk (^4.0.0)
- Rework getting browser name (see `README.md`)
- Drop `Python 3.10` support
- Drop `pytest-variables` support (now use pytest options to provide browser name)
- Add `ruff` and `cspell` linters
- Small code and structure improvements

## Version 1.2.0

- Fix `filelock` blocking for parallel tests run

## Version 1.1.1

- The remote browser name is now also looked up in the `stash` attribute
  in `pytest.Config` to add support for ^3.0.0 versions of `pytest-variables`

## Version 1.1.0

- Refactor the use of `pytest-variables` in `QasePlugin`
- Added description of pytest options to docs

## Version 1.0.0

- Initial release

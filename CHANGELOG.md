# Version history

We follow [Semantic Versions](https://semver.org/).

# Version 2.2.1
- Fix skipping reports for already passed tests

# Version 2.2.0
- Replace `qaseio` to `qase-api-client` because first one was [deprecated](https://github.com/qase-tms/qase-python#deprecated)

# Version 2.1.2
- Update `DebugInfo.generate_debug_comment`: set default values for `screenshot_url`
  and `html_url`

# Version 2.1.1
- Improve exception handling in `DebugInfo`

# Version 2.1.0
- Update environment tools
- Update pyproject.toml for backward compatibility (freeze arrow on 1.2.3 version)

# Version 2.0.0

- Use updated `qaseio` sdk (^4.0.0)
- Rework getting browser name (see `README.md`)
- Drop `Python 3.10` support
- Drop `pytest-variables` support (now use pytest options to provide browser name)
- Add `ruff` and `cspell` linters
- Small code and structure improvements

# Version 1.2.0

- Fix `filelock` blocking for parallel tests run

# Version 1.1.1

- The remote browser name is now also looked up in the `stash` attribute
  in `pytest.Config` to add support for ^3.0.0 versions of `pytest-variables`

# Version 1.1.0

- Refactor the use of `pytest-variables` in `QasePlugin`
- Added description of pytest options to docs

## Version 1.0.0

- Initial release

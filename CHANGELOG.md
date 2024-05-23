# Version history

We follow [Semantic Versions](https://semver.org/).

# Version 2.0.0

- Use updated `qaseio` sdk (^4.0.0)
- Drop `Python 3.10` support
- Drop `pytest-variables` support (now use pytest options to provide browser name)
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

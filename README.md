# pytest-qaseio

[![Build Status](https://github.com/saritasa-nest/pytest-qaseio/workflows/checks/badge.svg?branch=main&event=push)](https://github.com/saritasa-nest/pytest-qaseio/actions?query=workflow%3Achecks)
[![Python Version](https://img.shields.io/pypi/pyversions/pytest-qaseio.svg)](https://pypi.org/project/pytest-qaseio/)

Another implementation of Pytest plugin for Qase.io integration

Our features:

* Extended error report for Selenium (screenshot, html and browser logs)
* Strict case ids validations
* Instead of case ids, it uses direct links to cases
* Custom file storage for attachments
* Provide URL of test run starter
* Most of configuration options use environment variables

Not supported currently:

* Adding results to existing test runs
* Test steps

## Installation

```bash
pip install pytest-qaseio
```

## Configuration

To work with plugin you have to provide the following environment variables:

* `QASE_PROJECT_CODE` - Code of your Qase.io project

* `QASE_TOKEN` - API token to interact with Qase.io runs via API

A few more configuration environment variables are also available:
`QASE_PLAN_ID`, `QASE_ENVIRONMENT_ID` and `QASE_URL_CUSTOM_FIELD_ID`.

Specifying plan allows to create run "from template".
New run will contain all cases from plan + cases that specified in tests

`QASE_URL_CUSTOM_FIELD_ID` and `RUN_SOURCE_URL`  variables allow to specify custom
field ID to store the [URL of the run source](#set-run-source-url)

## Usage

To connect your python test with `Qase.io` just use `qase` mark and specify test
case url:

```python
import pytest

@pytest.mark.qase("https://app.qase.io/case/DEMO-1")
def test_demo():
    """Check qaseio plugin works as expected."""
```

Since this package is mostly used for selenium tests, it expects to get browser
name to use in Qase.io test run name and in attachments path. By default you can
provide it using `--webdriver` flag. But you can also override
`pytest_qase_browser_name` hook to implement some custom logic.
Here's an example of custom hook:

```python
@pytest.hookimpl(tryfirst=True)
def pytest_qase_browser_name(config: pytest.Config) -> str:
    """Try to get browser name from `webdriver` pytest option."""
    return config.getoption("--webdriver")

```

To enable plugin use flag `--qase-enabled`.

```bash
pytest tests/ --qase-enabled --webdriver=chrome
```

## Work with Selenium

This plugin expects to be used with selenium and provides additional debug
info from browser. To make it possible, prepare fixture that provides webdriver
and use the following snippet to set `_webdriver` attribute for each test:

```python
@pytest.fixture(autouse=True)
def annotate_node_with_driver(self, request: SubRequest):
  """Add webdriver instance to test, that later will be used to debug info.

  This fixture detects whether a test or its parent is using a selenium
  webdriver, and marks the node with the webdriver instance.

  """
  for fixture_name in request.fixturenames:
    if fixture_name.endswith("webdriver") and isinstance(
      request.getfixturevalue(fixture_name), selenium_webdriver.Remote,
    ):
      request.node._webdriver = request.getfixturevalue(fixture_name)
```

## File storage

`pytest-qaseio` plugin provides additional debug information in comment for
failed tests. It prepares browser log, html and screenshot. To store this
files plugin uses file storage. By default plugin provides and uses `QaseFileStorage`
that uploads files to Qase.io S3 bucket via attachments API.
If you don't want to upload files, just set `--qase-file-storage=None` option.

You can also provide your custom file storage. To do this, follow the next steps:

1) Prepare object that implements `save_file_obj()` method according to `storage.FileProtocol`
2) Override `pytest_qase_file_storages` hook and add mapping to your storage
3) Use `--qase-file-storage` option to specify name of you storage

**Note**: Keep in mind that `None` choice is reserved for disabling storages.

Example:

```python

## storages.py

class S3FileStorage:

  def __init__(self, **credentials): ...

  def save_file_obj(self, content: bytes, filename: str, **kwargs) -> str:
    """Upload file to S3 and get it's url."""
    self.s3_client.put_object(
        Body=content,
        Bucket=self.bucket,
        Key=filename,
        **kwargs,
    )
    return f"{self.s3_client.meta.endpoint_url}/{self.bucket}/{filename}"

## conftest.py

@pytest.hookimpl(tryfirst=True)
def pytest_qase_file_storages() -> dict[str, qase_storages.FileStorage]:
    """Override file storages to use custom S3 bucket."""
    return {
        "s3": S3FSStorage(),
    }

## Run tests
$ pytest --qase-enabled --qase-file-storage=s3

```

You can also override `qase_file_storage` to set storage for part of tests
(or for all in global `conftests.py`):

```python
@pytest.fixture
def qase_file_storage() -> storage.FileProtocol:
  return S3FileStorage()
```

## Pytest options

Plugin provides two pytest options:

`--qase-enabled` - use turn on qase plugin and run your tests with Qase.io integration
`--qase-file-storage` - allows to choose storage to upload additional debug info
   for failed tests. `None` and `qase` choices are available by default.

## Set run source url

Sometimes it might be useful to see the source that runs tests. If you need this,
you have to [create custom field](https://help.qase.io/en/articles/5563701-custom-fields)
for your Qase.io project.

Then you need to find `ID` of this field and set `QASE_URL_CUSTOM_FIELD_ID`
environment variable. To find custom field ID:

 1. open project -> `Test runs` -> `Start new test run`
 2. inspect custom field section with browser dev tools
 3. find label or text area of this custom field and you will see id in next
    format `cf-1-31`. The last number (`31`) is ID.

Finally, provide `RUN_SOURCE_URL` environment variable with URL to test run.

## License

[MIT](https://github.com/saritasa-nest/pytest-qaseio/blob/main/LICENSE)

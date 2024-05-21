class BaseQasePluginException(Exception):
    """Represent BaseQasePlugin exception."""

    message: str = ""

    def __init__(self, *args, message: str = "") -> None:
        super().__init__(*args)
        if message:
            self.message = message


class InvalidCaseId(BaseQasePluginException):
    """Exception that signifies that incorrect case was set for test."""

    message = "Tests have incorrect cases ids. Please check logs"


class DuplicatingCaseId(BaseQasePluginException):
    """Exception that signifies that incorrect case was set for test."""

    def __init__(self, duplicating_ids: list[int], *args) -> None:
        ids = ", ".join(str(i) for i in duplicating_ids)
        super().__init__(
            *args,
            message=f"Duplicating qase IDs found: {ids}",
        )


class MultipleIDsForTest(BaseQasePluginException):
    """Exception that signifies that single test marked with multiple IDs.

    Each test should be associated with exactly 1 case from qase.io for
    following reasons:

    * Atomic checks. It's easier to debug and fix
    * Adding support of multiple IDs to plugin will make it more complex.

    """

    message = "Multiple qase IDs associated with single test"


class RunNotConfigured(BaseQasePluginException):
    """Exception that signifies that test run not configured."""

    message = "Test run not configured"

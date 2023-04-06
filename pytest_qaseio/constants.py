RUN_NAME_TEMPLATE = "({env}) Automated Test Run {browser} {date}"
REPORT_FOLDER_TEMPLATE = "{env}/{browser}/run-{id}/{test_name}"

TEST_PASSED = "Test Passed"
TEST_FAILED = "Test Failed, on `{when}`"

FAILED_TEST_REPORT_TEMPLATE = """
---

* URL: [URL]({url})
* Browser log: [Browser log]({browser_log_url})
* Screenshot: ![driver screenshot]({screenshot_url})
* HTML: [HTML file]({html_url})

---
"""

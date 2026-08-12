# Test IT TMS importers
![Test IT](https://raw.githubusercontent.com/testit-tms/importers/main/images/banner.png)

[![Release
Status](https://img.shields.io/pypi/v/testit-importer-allure?style=plastic)](https://pypi.python.org/pypi/testit-importer-allure)
[![Downloads](https://img.shields.io/pypi/dm/testit-importer-allure?style=plastic)](https://pypi.python.org/pypi/testit-importer-allure)
[![GitHub contributors](https://img.shields.io/github/contributors/testit-tms/importers?style=plastic)](https://github.com/testit-tms/importers)

# Allure report

## Getting Started

### Installation
```
pip install testit-importer-allure
```

## Usage
### Configuration

Use the command `testit --help` to view the configuration setup help:
```
testit --url <url>
testit --privatetoken <token>
testit --projectid <id>
testit --configurationid <id>
```

And fill parameters with your configuration, where:  
`url` - location of the TMS instance  
`privatetoken` - API secret key  

1. go to the https://{DOMAIN}/user-profile profile  
2. copy the API secret key

`projectid` - id of project in TMS instance

1. create a project
2. open DevTools -> network
3. go to the project https://{DOMAIN}/projects/{PROJECT_GLOBAL_ID}/tests
4. GET-request project, Preview tab, copy id field  

`configurationid` - id of configuration in TMS instance  

1. create a project  
2. open DevTools -> network  
3. go to the project https://{DOMAIN}/projects/{PROJECT_GLOBAL_ID}/tests  
4. GET-request configurations, Preview tab, copy id field 

### Importing

Use the command `testit --resultsdir allure-results --testrunname <name>` to specify the directory with Allure report results and create new test run with the specified name in TMS instance.
<br>The `--testrunname` parameter is optional. The default name of testrun is <em>"AllureRun"</em>
<br>Or use the command `testit --resultsdir allure-results --testrunid <id>` to specify the directory with Allure report results and id of test run in TMS instance.
<br>**Important:** This command initiates the import.

### Test run tags and links

You can attach **test run** tags and links (e.g. CI job URL) so they are visible in TMS while the run is still in progress.

| Source | Tags | Links |
|--------|------|-------|
| CLI | `--testruntags` / `-trt` | `--testrunlinks` / `-trl` |
| Env | `TMS_TEST_RUN_TAGS` | `TMS_TEST_RUN_LINKS` |
| `connection_config.ini` `[testit]` | `testRunTags` | `testRunLinks` |

Priority: env > CLI > ini. Empty / omitted values mean "do not change".

**Tags** — comma-separated or JSON array:

```text
smoke,nightly
```

```json
["smoke", "nightly"]
```

**Links** — JSON array (`url` required; `title`, `description`, `type` optional):

```json
[
  {
    "url": "https://gitlab.example.com/group/project/-/jobs/12345",
    "title": "CI Job",
    "type": "Related"
  }
]
```

Supported link types: `Related`, `BlockedBy`, `Defect`, `Issue`, `Requirement`, `Repository`.

Behaviour:

- **New test run** (`--testrunname` / default): tags and links are sent in the create request.
- **Existing test run** (`--testrunid`): tags and links are merged at the start of import (existing items are kept; duplicates by tag name / link URL are skipped).

Example (CI job URL + tags):

```bash
testit --resultsdir allure-results \
  --testruntags smoke,nightly \
  --testrunlinks "[{\"url\":\"$CI_JOB_URL\",\"title\":\"CI Job\",\"type\":\"Related\"}]"
```

Or via env:

```bash
export TMS_TEST_RUN_TAGS=smoke,nightly
export TMS_TEST_RUN_LINKS='[{"url":"https://gitlab.example.com/.../jobs/12345","title":"CI Job","type":"Related"}]'
testit --resultsdir allure-results
```

# Contributing

You can help to develop the project. Any contributions are **greatly appreciated**.

* If you have suggestions for adding or removing projects, feel free to [open an issue](https://github.com/testit-tms/importers/issues/new) to discuss it, or directly create a pull request after you edit the *README.md* file with necessary changes.
* Please make sure you check your spelling and grammar.
* Create individual PR for each suggestion.
* Please also read through the [Code Of Conduct](https://github.com/testit-tms/importers/blob/master/CODE_OF_CONDUCT.md) before posting your first idea as well.

# License

Distributed under the Apache-2.0 License. See [LICENSE](https://github.com/testit-tms/importers/blob/master/LICENSE.md) for more information.


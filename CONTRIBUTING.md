# How to contribute

## Dependencies

We use [poetry](https://github.com/python-poetry/poetry) to manage the dependencies.

To install them you would need to run `install` command:

```bash
poetry install
```

To activate your `virtualenv` run `poetry shell`.

## One magic command

Run `make check` to run everything we have!

## Style checks

We use `flake8` for quality control.

To run linting:

```bash
flake8 .
```

## Type checks

We use `mypy` to run type checks on our code.
To use it:

```bash
mypy pytest_qaseio
```

## Submitting your code

We use [trunk based](https://trunkbaseddevelopment.com/) development.

What the point of this method?

1. We use protected `main` branch,
   so the only way to push your code is via pull request
2. We use issue branches: to implement a new feature or to fix a bug
   create a new branch named `issue-$TASKNUMBER`
3. Then create a pull request to `main` branch
4. We use `git tag`s to make releases, so we can track what has changed
   since the latest release

So, this way we achieve an easy and scalable development process
which frees us from merging hell and long-living branches.

In this method, the latest version of the app is always in the `main` branch.

### Before submitting

Before submitting your code please do the following steps:

1. Add any changes you want
2. Add tests for the new changes
3. Edit documentation if you have changed something significant
4. Update `CHANGELOG.md` with a quick summary of your changes
5. Run `mypy` to ensure that types are correct
6. Run `flake8` to ensure that style is correct

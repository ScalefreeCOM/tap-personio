# tap-personio by [Scalefree International GmbH](https://www.scalefree.com)

[<img src="https://user-images.githubusercontent.com/78537603/191483803-8cd4fc72-54a1-45f6-ab39-d798ec83e4c9.jpg" width=50% align=right>](https://www.scalefree.com)


`tap-personio` is a Singer tap for Personio.

This tap:

- Pulls raw data from (http://personio.com)
- Extracts the following resources:
  - attendances
  - employees
- Outputs the schema for each resource
- Incrementally pulls data based on the input state (not implemented yet)

## Installation

- [ ] `Developer TODO:` Update the below as needed to correctly describe the install procedure. For instance, if you do not have a PyPi repo, or if you want users to directly install from your git repo, you can modify this step as appropriate.

```bash
pipx install tap-personio
```

## Configuration

### Accepted Config Options

- [ ] `Developer TODO:` Provide a list of config options accepted by the tap.

A full list of supported settings and capabilities for this
tap is available by running:

```bash
tap-personio --about
```

### Source Authentication and Authorization

- [ ] `Developer TODO:` If your tap requires special access on the source system, or any special authentication requirements, provide those here.

## Usage

You can easily run `tap-personio` by itself or in a pipeline using [Meltano](https://meltano.com/).

### Executing the Tap Directly

```bash
tap-personio --version
tap-personio --help
tap-personio --config CONFIG --discover > ./catalog.json
```

## Developer Resources

- [ ] `Developer TODO:` As a first step, scan the entire project for the text "`TODO:`" and complete any recommended steps, deleting the "TODO" references once completed.

### Initialize your Development Environment

```bash
pipx install poetry
poetry install
```

### Create and Run Tests

Create tests within the `tap_personio/tests` subfolder and
  then run:

```bash
poetry run pytest
```

You can also test the `tap-personio` CLI interface directly using `poetry run`:

```bash
poetry run tap-personio --help
```

### Testing with [Meltano](https://www.meltano.com)

_**Note:** This tap will work in any Singer environment and does not require Meltano.
Examples here are for convenience and to streamline end-to-end orchestration scenarios._

Your project comes with a custom `meltano.yml` project file already created. Open the `meltano.yml` and follow any _"TODO"_ items listed in
the file.

Next, install Meltano (if you haven't already) and any needed plugins:

```bash
# Install meltano
pipx install meltano
# Initialize meltano within this directory
cd tap-personio
meltano install
```

Now you can test and orchestrate using Meltano:

```bash
# Test invocation:
meltano invoke tap-personio --version
# OR run a test `elt` pipeline:
meltano elt tap-personio target-jsonl
```

---

Copyright &copy; 2022 Scalefree International

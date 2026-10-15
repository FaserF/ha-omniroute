# Development

## Local Setup

Clone the repository and install development dependencies:

```bash
git clone https://github.com/FaserF/ha-omniroute.git
cd ha-omniroute
make install
```

## Running Tests

Run the full pytest suite with coverage:

```bash
make test
```

## Linting & Type Checking

```bash
make lint
```

## Documentation

To test and build documentation locally:

```bash
pip install -r docs/requirements.txt
mkdocs serve
```

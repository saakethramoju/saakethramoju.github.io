# Installation

## Install using `pip`

FullFlow is a native Python package available directly from PyPI.

Install the latest release with:

```bash
pip install fullflow
```

or 

```bash
pip3 install fullflow
```

depending on your version of python.

## Upgrade FullFlow

To upgrade an existing installation:

```bash
pip install --upgrade fullflow
```

## Development Installation

To install the latest development version from GitHub:

```bash
git clone https://github.com/saakethramoju/FullFlow.git
cd FullFlow
pip install -e .
```

An editable installation (`-e`) allows you to modify the source code and immediately test changes without reinstalling the package.

## Verify Installation

Create a file named `test.py`:

```python
from fullflow import *

print("FullFlow installed successfully!")
```

Run:

```bash
python test.py
```

If the script executes without errors, FullFlow has been installed successfully.

## Dependencies

FullFlow automatically installs all required dependencies, including:

- NumPy
- SciPy
- ThermoProp
- rich
- RocketCEA
- pandas
- openpyxl

No additional setup is required for most users.
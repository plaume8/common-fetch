# common-fetch

Closing the gap between data providers and data consumers.

[![PyPI](https://img.shields.io/pypi/v/common-fetch-loader)](https://pypi.org/project/common-fetch-loader/)
[![Python](https://img.shields.io/pypi/pyversions/common-fetch-loader)](https://pypi.org/project/common-fetch-loader/)
[![License](https://img.shields.io/pypi/l/common-fetch-loader)](LICENSE)

---

## Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [Getting Started: Pip Package User](#-getting-started-pip-package-user)
- [Getting Started: Developer](#-getting-started-developer)
  - [Data Loader](#-data-loader)
  - [Data Server](#-data-server)
- [Miscellaneous](#-miscellaneous)

---

<a id="overview"></a>

## 	🔎 Overview

Data scientists routinely work with datasets that come from different sources, in different formats, 
and behind different access mechanisms. Reconciling them costs time that would be better spent on analysis.

**common-fetch** is a lightweight, white-box framework that closes this gap. 
It lets a data provider publish heterogeneous datasets through a single HTTP API, 
and lets consumers retrieve them through one consistent Python interface.
Adding a new dataset requires a YAML schema and a single Python function, nothing else.

The framework consists of two parts:

| Component | What it is | Who uses it |
|---|---|---|
| `common-fetch-loader` | A pip package that provides the client-side API | Researchers and analysts consuming data |
| `cf-server` | A FastAPI application that prepares and serves the data | Developers publishing data |

To run your own instance, fork this repository, add your datasets, and deploy the server. 
Everything you need is described in the [Developer guide](#-getting-started-developer) below.

<img src="others/system_overview_high_level.svg" width="600" />

---

## ✨ Key Features

### Easy data fetching

The `common-fetch-loader` package provides a high-level API for accessing connected datasets, 
so users can retrieve complex data with very little boilerplate. It offers:
- Standardized getter functions that behave the same way across datasets
- Consistent return formats (typically pandas DataFrames)
- Optional, dataset-specific parameters for finer control
- Transparent local caching, so repeated calls do not hit the API twice

### Easy integration of new data sources

On the server side, every dataset is described by exactly two artifacts:
- `schema`: which defines the dataset's metadata and the structure of a valid request
- `retriever`: which performs the actual data acquisition and preprocessing

This separation keeps integrations structured and maintainable. 
Once both artifacts exist, the dataset is automatically exposed through the API and available to package users,
and no changes to the server code are required.

> A working example implementation can be found here: [TUM EMT Data Loader](https://gitlab.lrz.de/energy-management-technologies-public/data-loader)

---

##	🚀 Getting Started

This section contains two separate guides, depending on how you intend to use the framework:

1. **[Pip package users](#-getting-started-pip-package-user)**: researchers or analysts who want to consume data via the Python package.
2. **[Developers](#-getting-started-developer)**: developers who want to fork the framework, add new data sources, or work on the backend infrastructure.

---

## 📦 Getting Started: Pip Package User

Follow the steps below if you only want to use `common-fetch-loader` to access existing data sources.

##### 1. Installation

Prerequisite: Python >= 3.10
```shell
pip install common-fetch-loader
```
The package is installed as `common-fetch-loader` but imported as `cfl`.

##### 2. Connect and authenticate

Point the client at a server instance and authenticate with your API key:
```python
import cfl

cfl.set_host("<cf_server_address>")
cfl.authenticate("<your_api_key>")
```

##### 3. Discover the available datasets

To list all datasets that the connected server currently exposes:
```python
cfl.get_available_dataset_ids()
```

##### 4. Inspect a dataset

Every dataset provides a `get_description()` function, which returns a string summarizing the dataset and its request parameters:
```python
df = cfl.<dataset_id>.get_description()
```

### 5. Fetch data

For each available dataset, specific data getter functions are provided.
You can explore available functions using autocomplete by typing `cfl.<dataset_id>.` into your IDE (e.g. Jupyter Notebook).
Checkout the function documentation to learn more about the functions specific parameters.

Every getter function:
1. Fetches the data from the server
2. Caches the data locally
3. Returns it in a convenient format (e.g. a pandas DataFrame)

**Example:**
```python
df = cfl.dummy_dataset.get_dummy_data(year=2025)
```

The local cache is stored in the `/tmp` directory. If a getter is called again with the same parameters,
the data is loaded from the cache instead of being fetched again, saving both time and API costs.

---

## 🛠️ Getting Started: Developer

<img src="others/system_overview_model.svg" />

The system/repository is split into two packages:
- **`data_loader`**: the pip package shipped to end users who want to access the data.
- **`data_server`**: a FastAPI instance containing the data preparation and serving logic.

---

### 🔌 Data Loader

The `data_loader` package follows a **leaky-facade pattern** with two layers:

- **Low-level layer (yellow).** Provides the core data retrieval functionality. This layer alone already gives access to every dataset and every server capability. See `basics.py` and `data.py` for details.
- **High-level layer (orange).** Provides convenient, dataset-specific helper functions built on top of the low-level layer. This is what most end users interact with.

The layer is "leaky" by design: the high-level helpers cover the common cases, 
but the low-level API remains available whenever a user needs something the helpers do not expose.

#### Adding high-level functionality for a dataset

When a new dataset is added to the `data_server`, it is immediately reachable through the low-level layer. 
Adding high-level helpers is optional but strongly recommended, as it is what makes the dataset even more easily accessible.

To do so:
1. Create a new folder in `custom_data_getters/` named after the `<dataset_id>`.
2. Add a Python file `<dataset_id>.py` inside that folder containing all functions the user should have access to.
3. Ensure every function has a clear, self-explanatory docstring.
4. Include a `get_description()` function, consistent with all other dataset getters.
5. Add an `__init__.py` file that exports all public functions.
6. Update the top-level `__init__.py` of the `cfl` pip package accordingly.

> **Tip:** Look at existing example implementations for reference. 

#### Publishing a new package version

After making changes to the package, publish a new version to PyPI:
1. Open `pyproject.toml` and increment the `version` field OR if this directory is forked: update all fields to your own pip package
2. Ensure `build` is installed: `pip install build`
3. From the `/data_loader` directory, run: `python3 -m build && twine upload dist/*`

> Further reading: [general pip introduction](https://packaging.python.org/en/latest/tutorials/packaging-projects/)

---

### 🗄️ Data Server

The data server is also split into two layers:

- **API layer (blue).** Contains all [FastAPI](https://fastapi.tiangolo.com/#installation) endpoints and the server configuration. `main.py` holds the complete FastAPI setup.
- **Retriever layer (purple).** Contains the dataset-specific retriever logic and data handling.

#### Architecture overview

The overall idea is quite simple:

1. A client sends a request to the `/data` endpoint including a defined request schema.
2. The `data_server` receives the request object and calls the matching retriever function for the specified dataset.
3. The retriever processes the request, fetching, parsing, and cleaning the data, then stores the prepared files in an `outbox` directory and returns their filenames.
4. The FastAPI server returns those filenames to the client.
5. The client downloads each file via the `/data/download/{data_file}` endpoint.

> **Tip:** See the pip package implementation to understand how the data retrieval works on the client side — it uses straightforward Python and is simpler than it looks.

**Additional endpoints:**
- `/dataset_ids`: Returns an array of all available dataset IDs.
- `/schema/{dataset_id}`: Returns the schema for a given dataset, including basic info and a request object boilerplate.

##### Adding a New Dataset

To add a new dataset and to make available via the `data_server` for the API and pip package end users please follow the following steps:

1. Choose a unique `dataset_id` for the new dataset (e.g. `dummy_dataset`).
2. Create a folder `/raw_data/<dataset_id>/` and add all raw data files to it.
3. Create a schema file `/schemas/<dataset_id>.yaml` with the following fields:
   - `dataset_id`: The chosen dataset ID.
   - `description`: A short description of the dataset.
   - `request_logic`: A short explanation of the request parameters.
   - `request`: All parameters of the request object (boilerplate).
4. Create a retriever at `/retrievers/<dataset_id>_retriever.py` implementing the following function signature:
    ```python
       def retrieve(outbox: Path, request: Optional[dict[str, Any]]) -> list[str]:
           pass
    ```
   > **Tip:** See `dummy_dataset_retriever.py` for a minimal working example.
5. That's it ... the server will now recognise the new dataset, its request schema, and know which retriever to call.

#### Running the server locally

To test the implementation locally, you can simply run a local FastAPI instance by executing:
```bash
cd data-server/src/cf_server
export PYTHONPATH="$PWD"
fastapi dev main.py
```
The server then runs at [http://127.0.0.1:8000](http://127.0.0.1:8000), 
with interactive API documentation at `/docs`. 
Use Postman or any other HTTP client to exercise the endpoints, or open `/tests/dummy_testing.ipynb` for a dummy notebook.

---

## 🧩 Miscellaneous

### Manage API Keys

We implemented a simple Python script called `api_keys_management` for managing API keys. 
See `/data_server/src/cf_server/auth/keys/api_keys_management.py` for details.

### Execute Local Server Tests

Simple system tests are implemented in `/tests/test_system.py`. 
These tests call and verify all low-level API functions from the pip package using dummy data. 
While they do not test the client or server side in depth, they verify base functionality through black-box testing.

To run the tests:
1. Make sure all dependencies are installed (`pip install -r requirements.txt`)
2. Navigate to `/data-loader` or `tests` directory
3. Run: `pytest`

---

##	👤 Authors

[Linus Sander](mailto:linus.sander@icloud.com)  

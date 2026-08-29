# common-fetch

Closing the gap between data providers and consumers.

---

## Key Features

### Addressed Problem

Data scientists frequently rely on heterogeneous datasets originating from different sources, formats, and access mechanisms. 
For a lot of domains and use cases, it would be highly beneficial to access these datasets through a standardized and unified API. 

The __common-fetch__ framework provides a simple white box framework for publishing data 
through a publicly accessible API and a Python package that enables consistent and convenient access.
Beyond that, it makes it as easy as possible to upload new datasets and make them accessible via the API.

Simply fork this repository and run you own cf-server instance with your dedicated data.
All information required for the setup can be found in the Developers documentation below.

The whole framework consists of two main parts: the common-fetch-loader pip package and the common-fetch FastAPI Server

<img src="others/system_overview_high_level.svg" width="600" />

### Easy Data Fetching

The common-fetch-loader python package provides a high-level, easy-to-use API for accessing connected datasets.
This allows users to retrieve complex datasets with minimal boilerplate code.
It offers:
- Common, standardized data getter functions
- Consistent return formats (e.g. pandas DataFrames)
- Optional customization via dataset-specific parameters

### Easy Integration of New Data Sources

Adding new data sources is simplified through the use of two core concepts on the server side:
- `schemas`, which define the structure and metadata of datasets
- `retrievers`, which handle the actual data acquisition and preprocessing

This separation enables developers to integrate new data sources in a structured and maintainable way,
making them automatically available to end users of the pip package (see below for details).

> A working example implementation can be seen here: [TUM EMT Data Loader](https://gitlab.lrz.de/energy-management-technologies-public/data-loader)

---

## Getting Started

This section provides two separate guides for different end-users:
1.	_Pip Package Users_: researchers or analysts who want to consume data via the Python package
2.	_Developers_: contributors who want to extend the system, add new data sources, or work on the backend infrastructure

---

### Getting Started: Pip Package User

If you simply want to use the common-fetch-loader to access the available data sources, follow the steps below.

###### 1. Installation

Prerequisites:Python >= 3.10
```shell
pip install common-fetch-loader
```

###### 2. Server connection and authentication

Authenticate using the Data Loader authentication mechanism by providing your API key:
```python
import cfl 
cfl.set_host("<cf_server_address>")
cfl.authenticate("<your_api_key>")
```

###### 3. Check Available Data Sources

To get an overview of all currently available datasets, use:
```python
cfl.get_available_dataset_ids()
```

#### 4. Get Basic Information about a Dataset

Each dataset provides a get_description() function, 
which returns a simple string with all the basic information about the dataset.
```python
df = cfl.<dataset_id>.get_description()
```

#### 5. Fetch data

For each available dataset, specific data getter functions are provided.
You can explore available functions using autocomplete by typing `cfl.<dataset_id>.` into your IDE (e.g. Jupyter Notebook).
Checkout the function documentation to learn more about the functions specific parameters.

Each getter function:
- Fetches the requested data from the backend
- Caches the data locally
- Returns it in an appropriate format (e.g. a pandas DataFrame)

The local cache is stored in the `/tmp` directory. If a getter is called again with the same parameters,
the data is loaded from the cache instead of being fetched again, saving both time and API costs.

**Example:**
```python
df = cfl.dummy_dataset.get_dummy_data(year=2025)
```
---

### Getting Started: Developer

<img src="others/system_overview_model.svg" />

The system is divided into two packages: `data_loader` and `data_server`.
- **`data_loader`**: the pip package shipped to end users who want to access the data.
- **`data_server`**: a FastAPI instance containing the data preparation and serving logic.

---

#### Data Loader 

The `data_loader` package follows a **leaky-facade interface pattern** with two layers:
- **Yellow layer (low-level):** Provides the core functionality to retrieve data. In principle, this layer alone gives users access to all server functionality and datasets. Please have a look at the files `basics.py` and `data.py` for in detailed information.
- **Orange layer (high-level):** Provides more convenient, dataset-specific helper methods built on top of the yellow layer, making data access as easy as possible for end users.

##### Adding High-Level (Orange Layer) Functionality for a Dataset

If a new dataset has been added to the `data_server`, users can immediately access it via the yellow layer. 
However, to provide a better developer experience, orange layer helpers should also be implemented. 
To do so:
1. Create a new folder in `custom_data_getters/` named after the `<dataset_id>`.
2. Add a Python file `<dataset_id>.py` inside that folder containing all functions the user should have access to.
3. Ensure every function has a clear, self-explanatory docstring.
4. Include a `get_description()` function, consistent with all other dataset getters.
5. Add an `__init__.py` file that exports all public functions.
6. Update the top-level `__init__.py` of the `cfl` pip package accordingly.

> **Tip:** Look at existing example implementations for reference. 

##### Updating the Pip Package

After making changes to the package, publish a new version to PyPI:
1. Open `pyproject.toml` and increment the `version` field OR if this directory is forked: update all fields to your own pip package
2. Ensure `build` is installed: `pip install build`
3. From the `/data_loader` directory, run: `python3 -m build && twine upload dist/*`

> more: [general pip introduction](https://packaging.python.org/en/latest/tutorials/packaging-projects/)

---





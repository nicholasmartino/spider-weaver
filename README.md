# Predictive Urban Network Analysis

**Spider Weaver** is a high-level repository designed for spatial data aggregation and analysis across urban networks. This tool simplifies the process of gathering, processing, and analyzing spatial data to help predict key urban indicators, facilitating advanced data-driven insights into urban systems.

## Overview

The main functionality of this repository includes:
1. **Data Aggregation**: Collects and preprocesses spatial data from various open data sources.
2. **Metric Computation**: Aggregates network-based metrics across a sample spatial layer.
3. **Prediction Modeling**: Trains and evaluates a [RandomForestRegressor](https://scikit-learn.org/1.5/modules/generated/sklearn.ensemble.RandomForestRegressor.html#sklearn.ensemble.RandomForestRegressor) model to predict specified urban explanatory variables.
4. **BDD-Style Workflow**: Organizes the data pipeline and analysis steps using Behavior-Driven Development (BDD) testing with `behave`, allowing a structured and test-driven approach to data processing and analysis.

## Repository Structure

- **`data/`**: Directory for input spatial datasets, including raw data from open sources and processed data files.
- **`models/`**: Stores the trained model objects and any related configuration files.
- **`scripts/`**: Contains Python scripts for data aggregation, metric computation, and model training and evaluation.
- **`tests/`**: Holds BDD-style tests that validate data processing and prediction outputs.
- **`requirements.txt`**: Lists required dependencies to run the code in this repository.
- **`README.md`**: This document, providing an overview and instructions for setup and usage.

## Installation

To set up the environment and install all necessary dependencies:

```bash
pip install -r requirements.txt
```

## Usage

1. **Data Processing and Aggregation**: Use scripts within the `scripts/` directory to load, preprocess, and aggregate data. The exact parameters for each script are detailed in each script’s docstring.

2. **Run BDD-Style Tests**:
   The repository uses BDD tests to ensure reliability in the data processing and prediction steps. To run these tests with your own data, use:

   ```bash
   behave
   ```

   These tests will validate various parameters, expected data formats, and model results. Refer to `tests/` for specific test case implementations.

3. **Train and Evaluate the Model**:
   The repository includes code for training a `RandomForestRegressor` model on the aggregated data. Once trained, the model assesses specific explanatory variables and outputs key insights on network-based predictions. Check the `scripts/` directory for details on model parameters and configuration options.

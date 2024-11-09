# Predictive Urban Network Analysis

**Spider Weaver** is a high-level repository designed for spatial data aggregation and analysis across urban networks. This tool simplifies the process of gathering, processing, and analyzing spatial data to help predict key urban indicators, facilitating advanced data-driven insights into urban systems.

## Overview

The main functionality of this repository includes:

1. **Data Aggregation**: Collects and preprocesses spatial data from various open data sources.
2. **Metric Computation**: Aggregates network-based metrics across a sample spatial layer.
3. **Prediction Modeling**: Trains and evaluates a [RandomForestRegressor](https://scikit-learn.org/1.5/modules/generated/sklearn.ensemble.RandomForestRegressor.html#sklearn.ensemble.RandomForestRegressor) model to predict specified urban explanatory variables.
4. **BDD-Style Workflow**: Organizes the data pipeline and analysis steps using Behavior-Driven Development (BDD) testing with `behave`, allowing a structured and test-driven approach to data processing and analysis.

## Repository Structure

- **`citymodel/`**: Core object model for representing and simulating urban environments.
- **`data/`**: Folder was excluded from GitHub repo due to the large file sizes. Contains spatial datasets:
  - **Raw data**: Original data from open sources.
  - **Processed data**: Refined datasets ready for analysis and model input.
- **`features/`**: Behavior-driven development (BDD) tests for validating data processing workflows and prediction outcomes.
- **`learnkit/`**: Machine learning module for network analysis, prediction models, and related scripts.
- **`requirements.txt`**: Defines all necessary dependencies for seamless execution of the repository's code.

## Installation

To set up the environment and install all necessary dependencies:

```bash
pip install -r requirements.txt
```

## Usage

1. **Link Data Folder**

   ```bash
   ln -s "path-to-data" data
   ```

2. **Data Processing and Aggregation**: Use scripts within the `scripts/` directory to load, preprocess, and aggregate data. The exact parameters for each script are detailed in each script’s docstring.

3. **Run BDD-Style Tests**:
   The repository uses BDD tests to ensure reliability in the data processing and prediction steps. To run these tests with your own data, use:

   ```bash
   behave
   ```

   These tests will validate various parameters, expected data formats, and model results. Refer to `tests/` for specific test case implementations.

4. **Train and Evaluate the Model**:
   The repository includes code for training a `RandomForestRegressor` model on the aggregated data. Once trained, the model assesses specific explanatory variables and outputs key insights on network-based predictions. Check the `scripts/` directory for details on model parameters and configuration options.

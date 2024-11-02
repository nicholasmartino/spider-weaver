# Created by nicholasmartino at 2023-10-18

Feature: Urban Space Dynamics Prediction

  # As an urban researcher,
  # I want to use georeferenced data to train a predictive model,
  # So that I can accurately predict key indicators related to walkability and affordability in urban areas,
  # And identify spatial indicators that significantly influence these dynamics

  Background:
    Given a dataset of georeferenced parcel geometries within the Metro Vancouver Regional District

  Scenario Outline: Training a predictive model with spatial data
    When the dataset includes valid quantitative and georeferenced data
    Then use 80% of the available data to train a random forest model to predict <dependent> variable

    Examples:
      | dependent                  |
      | walkability_r1600_sum_flat |
      | rent_price_r1600_ave_flat  |

  Scenario: Predicting dependent variables with a trained model
    Given a predictive model trained
    Then assess predictive accuracy based on the test data
    And rank explanatory variables by permutation importance

  Scenario: Exporting maps to external path
    Given a predictive model trained
    Then plot maps of 6 most important variables
    And copy outputs to manuscript path

  Scenario: Plot correlation matrix
    Given a predictive model trained
    Then plot a correlation matrix of 6 most important features
    And copy outputs to manuscript path  

  Scenario: Exporting significance to external path
    Given a predictive model trained
    Then plot significance charts of 6 most important variables
    And copy outputs to manuscript path

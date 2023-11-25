# Created by nicholasmartino at 2023-10-18

Feature: Urban Space Dynamics Prediction

  As an urban researcher,
  I want to use georeferenced data to train a predictive model,
  So that I can accurately predict key indicators related to walkability and affordability in urban areas,
  And identify spatial indicators that significantly influence these dynamics.

  Background:
    Given a dataset of georeferenced parcel geometries within the Metro Vancouver Regional District

  Scenario Outline: Training a predictive model with spatial data
    When the dataset includes valid quantitative and georeferenced data
    Then use 80% of the available data to train a random forest model to predict <dependent> variable

    Examples:
      | dependent            |
      | walk_r1600_ave_flat  |
      | price_r1600_ave_flat |

  Scenario: Predicting dependent variables with a trained model
    And a predictive model trained with a data split
    Then assess predictive accuracy based on the test data
    And rank significant predictors using partial dependence analysis

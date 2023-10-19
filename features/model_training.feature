# Created by nicholasmartino at 2023-10-18

Feature: Urban Space Dynamics Prediction

  As an urban researcher,
  I want to use georeferenced data to train a predictive model,
  So that I can accurately predict key indicators related to walkability and affordability in urban areas,
  And identify spatial indicators that significantly influence these dynamics.

  Scenario Outline: Predicting dependent variables with trained data
    Given a dataset of georeferenced parcel geometries within the Metro Vancouver Regional District
    And the dataset includes a valid series of explanatory and <dependent> spatial or quantitative variables
    When 80% of the available data is used to train a RandomForestRegressor model
    Then use the remaining data to test the accuracy of my trained model
    And extract the most significant spatial predictors of the <dependent> variables

    Examples:
      | dependent |
      | walkability        |
      | affordability      |
      | another_indicator  |

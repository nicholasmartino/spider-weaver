# Created by nicholasmartino at 2023-10-02

Feature: Spatial Metrics for City of Vancouver

  As an urban researcher,
  I want to spatially aggregate georeferenced data sources to property parcels
  So that I can train a predictive model.

  Background:
    Given parcel data located within Metro Vancouver Regional District

  Scenario Outline: Clean and Process Street Network
    Given <street_network> data located within Metro Vancouver Regional District
    When the geometry data of <street_network> is valid
    Then calculate segment length, straightness for <street_network>

    Examples:
      | street_network  |
      | network/walking |
      | network/cycling |
      | network/driving |

  Scenario Outline: Aggregate from Data Source to Parcel Along Street Network
    Given <data_source> data located within Metro Vancouver Regional District
    When the geometry data of <data_source> is valid
    And <series> is available in the <data_source> data
    Then join <series> within 800, 1600 meters from <data_source> to parcel layer via street network

    Examples:
      | data_source               | series                                        |
      | bc_assessment/parcel      | area_sqkm                                     |
      | bc_assessment/property    | n_use                                         |
      | bc_assessment/property    | age                                           |
      | bc_assessment/property    | NUMBER_OF_BEDROOMS                            |
      | census/dissemination_area | Population, 2016                              |
      | census/dissemination_area | Population density per square kilometre, 2016 |
      | census/dissemination_area | n_dwellings                                   |
      | census/dissemination_area | walk                                          |
      | craigslist/housing_rent   | price                                         |
      | open_street_map/amenities | amenity                                       |
      | network/walking           | length                                        |
      | network/cycling           | length                                        |
      | network/driving           | length                                        |
      | network/walking           | straight                                      |
      | network/cycling           | straight                                      |
      | network/driving           | straight                                      |

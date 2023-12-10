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
    Then <label> and join <series> within 800, 1600 meters from <data_source> to parcel layer via street network

    Examples:
      | data_source               | series                                        | label              |
      | bc_assessment/parcel      | area_sqkm                                     | parcel_area        |
      | bc_assessment/parcel      | perimeter                                     | parcel_perimeter   |
      | bc_assessment/property    | n_use                                         | land_use           |
      | bc_assessment/property    | age                                           | building_age       |
      | bc_assessment/property    | NUMBER_OF_BEDROOMS                            | bedroom_count      |
      | census/dissemination_area | Population, 2016                              | population         |
      | census/dissemination_area | Population density per square kilometre, 2016 | population_density |
      | census/dissemination_area | n_dwellings                                   | dwelling_count     |
      | census/dissemination_area | walk                                          | walkability        |
      | craigslist/housing_rent   | price                                         | rent_price         |
      | network/walking           | length                                        | walk_length        |
      | network/cycling           | length                                        | cycle_length       |
      | network/driving           | length                                        | drive_length       |
      | network/walking           | straight                                      | walk_straightness  |
      | network/cycling           | straight                                      | cycle_straightness |
      | network/driving           | straight                                      | drive_straightness |

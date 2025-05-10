# Created by nicholasmartino at 2023-10-02

Feature: Spatial Metrics for City of Vancouver

  As an urban researcher,
  I want to spatially aggregate georeferenced data sources to property parcels
  So that I can train a predictive model.

  Background:
    Given craigslist/housing_rent data located within Metro Vancouver Regional District

  Scenario Outline: Aggregate from Data Source to Sample Along Street Network
    Given <data_source> data located within Metro Vancouver Regional District
    When the geometry data of <data_source> is valid
    And <series> is available in the <data_source> data
    Then <operation> the <series> (<label>) within 1600 meters from <data_source> to samples via street network

    Examples:
      | data_source               | series                                        | label               | operation |
      | open_street_map/gps_walk  | count                                         | walkability         | sum       |
      | bc_assessment/parcel      | area_sqkm                                     | parcel_area         | ave       |
      | bc_assessment/property    | n_use                                         | land_use            | sum       |
      | bc_assessment/fabric      | PROPERTY_TYPE                                 | property_type       | sum       |
      | bc_assessment/fabric      | BUILDING_TYPE                                 | building_type       | sum       |
      | bc_assessment/fabric      | TOTAL_FINISHED_AREA                           | finished_area       | sum       |
      | bc_assessment/fabric      | LAND_SIZE                                     | land_size           | ave       |
      | bc_assessment/fabric      | LAND_DEPTH                                    | land_depth          | ave       |
      | bc_assessment/fabric      | NUMBER_OF_STOREYS                             | number_of_storeys   | sum       |
      | bc_assessment/fabric      | NUMBER_OF_STOREYS                             | number_of_storeys   | ave       |
      | bc_assessment/fabric      | NET_LEASABLE_AREA                             | net_leasable_area   | sum       |
      | bc_assessment/fabric      | GROSS_LEASABLE_AREA                           | gross_leasable_area | sum       |
      | bc_assessment/fabric      | STRATA_UNIT_AREA                              | strata_unit_area    | ave       |
      | bc_assessment/fabric      | STRATA_UNIT_AREA                              | strata_unit_area    | sum       |
      | bc_assessment/fabric      | AREA                                          | property_area       | sum       |
      | census/dissemination_area | Population, 2016                              | population          | sum       |
      | census/dissemination_area | Population density per square kilometre, 2016 | population_density  | ave       |
      | craigslist/housing_rent   | price                                         | rent_price          | ave       |
      | network/walking           | length                                        | walk_length         | ave       |
      | network/walking           | length                                        | walk_length         | sum       |
      | network/cycling           | length                                        | cycle_length        | sum       |
      | network/walking           | straight                                      | walk_straightness   | ave       |
      | network/cycling           | straight                                      | cycle_straightness  | ave       |
      | ubc/zoning                | fsr_max                                       | max_fsr             | ave       |
      | ubc/zoning                | fsr_max                                       | max_fsr             | max       |
      | ubc/zoning                | fsr_max                                       | max_fsr             | sum       |
      | ubc/zoning                | zc                                            | zone_classification | sum       |

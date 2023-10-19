# Created by nicholasmartino at 2023-10-02

Feature: Spatial Metrics for City of Vancouver

  As an urban researcher,
  I want to spatially aggregate georeferenced data sources to property parcels
  So that I can train a predictive model.

  Background:
    Given geospatial data located within Metro Vancouver Regional District

  Scenario Outline: Process Street Network Metrics
    Given <street_network> data located within Metro Vancouver Regional District
    When the geometry data of <street_network> is valid
    Then calculate segment length, straightness for <street_network>
    Examples:
      | street_network  |
      | network/walking |
      | network/cycling |
      | network/driving |

  Scenario Outline: Network Analysis - Census Dissemination Area
    Given census/dissemination_area data located within Metro Vancouver Regional District
    When the geometry data of census/dissemination_area is valid
    And <series> is available in the census/dissemination_area data
    Then join <series> within 400, 800, 1600 meters from census/dissemination_area to parcel layer via street network
    Examples:
      | series                                        |
      | Population, 2016                              |
      | Population density per square kilometre, 2016 |
      | n_dwellings                                   |

  Scenario Outline: Network Analysis - BC Assessment Property
    Given bc_assessment/property data located within Metro Vancouver Regional District
    When the geometry data of bc_assessment/property is valid
    And <series> is available in the bc_assessment/property data
    Then join <series> within 400, 800, 1600 meters from bc_assessment/property to parcel layer via street network
    Examples:
      | series             |
      | n_use              |
      | age                |
      | NUMBER_OF_BEDROOMS |

  Scenario Outline: Network Analysis - BC Assessment Parcel
    Given bc_assessment/parcel data located within Metro Vancouver Regional District
    When the geometry data of bc_assessment/parcel is valid
    And <series> is available in the bc_assessment/parcel data
    Then join <series> within 400, 800, 1600 meters from bc_assessment/parcel to parcel layer via street network
    Examples:
      | series    |
      | area_sqkm |

  Scenario Outline: Network Analysis - Open Street Map Amenities
    Given open_street_map/amenities data located within Metro Vancouver Regional District
    When the geometry data of open_street_map/amenities is valid
    And <amenity_type> is available in the open_street_map/amenities data
    Then join <amenity_type> within 400, 800, 1600 meters from open_street_map/amenities to parcel layer via street network
    Examples:
      | amenity_type     |
      | schools          |
      | hospitals        |
      | parks            |
      | shopping_malls   |
      | public_transport |
      | restaurants      |
      | banks            |
      | libraries        |
      | police_stations  |
      | post_offices     |

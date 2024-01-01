# Created by nicholasmartino at 2023-12-31

Feature: Data Gathering

  Scenario: Download GPS Traces
    Given a valid identification of a Metro Vancouver Regional District
    Then download and save GPS traces

  Scenario Outline: Clean and Process Street Network
    Given <street_network> data samples located within Metro Vancouver Regional District
    When the geometry data of <street_network> is valid
    Then calculate segment length, straightness for <street_network>

    Examples:
      | street_network  |
      | network/walking |
      | network/cycling |
      | network/driving |

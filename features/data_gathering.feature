# Created by nicholasmartino at 2023-12-31

Feature: Data Gathering

  Scenario Outline: Clean and Process Street Network
    Given <street_network> data samples located within Metro Vancouver Regional District
    When the geometry data of <street_network> is valid
    Then calculate segment length, straightness for <street_network>

    Examples:
      | street_network  |
      | network/walking |
      | network/cycling |
      | network/driving |

  Scenario Outline: Download GPS Traces
    Given a valid identification of a <place_name>
    Then download and save GPS traces

    Examples:
      | place_name                        |
      | Metro Vancouver Regional District |

def cucumber_to_markdown(input_path, output_directory):
    with open(input_path, "r") as file:
        lines = file.readlines()

    feature_name, scenarios = __extract_scenarios(lines)
    for scenario in scenarios:
        scenario_name, table_lines = scenario
        markdown = __convert_to_markdown(table_lines)
        output_filename = f"{feature_name}_{scenario_name}.md"
        __write_to_file(f"{output_directory}/{output_filename}", markdown)
        print(f"Markdown table written to {output_filename}")


def __extract_scenarios(lines):
    feature_name = ""
    current_scenario_name = ""
    scenarios = []
    table_lines = []
    in_examples = False

    for line in lines:
        if line.strip().startswith("Feature:"):
            feature_name = __process_line(line)
        elif line.strip().startswith("Scenario Outline:"):
            if current_scenario_name and table_lines:
                scenarios.append((current_scenario_name, table_lines))
                table_lines = []
            current_scenario_name = __process_line(line)
        elif line.strip() == "Examples:":
            in_examples = True
            continue
        elif in_examples and line.strip() == "":
            in_examples = False
            continue
        if in_examples:
            table_lines.append(line.strip())

    # Add the last scenario
    if current_scenario_name and table_lines:
        scenarios.append((current_scenario_name, table_lines))

    return feature_name, scenarios


def __process_line(line):
    return "_".join(
        [
            word
            for word in line.split(":", 1)[1].strip().split(" ")
            if not __is_preposition(word)
        ][:2]
    ).lower()


def __is_preposition(word):
    return word.lower() in ["and", "of", "from", "for"]


def __convert_to_markdown(table_lines):
    markdown_table = []
    for index, row in enumerate(table_lines):
        row_data = [elem.strip() for elem in row.split("|") if elem]
        markdown_row = "| " + " | ".join(row_data) + " |"
        markdown_table.append(markdown_row)
        if index == 0:
            markdown_table.append("|" + "---|" * len(row_data))
    return "\n".join(markdown_table)


def __write_to_file(filename, content):
    with open(filename, "w") as file:
        file.write(content)

import argparse
import re


def read_file(file_path):
    """Open a specified file, read the contents, and return them using python built-in methods

    Args:
        file_path (string): full path to the file including file name and extension

    Returns:
        list: list with each line (separated by \n) as an element
    """
    try:
        # Open the file in read mode
        with open(file_path, "r") as file:
            lines = file.readlines()
        return lines
    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found.")
    except Exception as e:
        print(f"An error occurred: {e}")


def write_file(file_path, lines, verbose=False):
    """Write the specified content to a file

    Args:
        file_path (string): full path to the output file including file name and extension
        lines (_type_): output to write to the file
        verbose (bool, optional): whether to enable verbose mode (print to stdout). Defaults to False.
    """
    if verbose:
        print(f"Writing to {file_path}...")

    with open(file_path, "w") as file:
        file.writelines(lines)


def test_write(lines):
    """Preview the changes that will be written to a file by printing to stdout

    Args:
        lines (string): text to be previewed
    """
    print(lines)


def find_linenum(lines, target_string, start=0, stop=0, verbose=False):
    # Find the line containing the target string
    index_of_target = -1
    if not stop:
        stop = len(lines)
    # print(f"Searching from line {start} to {stop}")
    for i in range(start, stop):
        if target_string in lines[i]:
            index_of_target = i
            break

    if index_of_target != -1:
        if verbose:
            print(
                f"The string '{target_string}' was found on line {index_of_target+1}."
            )
        return index_of_target
    else:
        if verbose:
            print(f"The string '{target_string}' was not found in the file.")
        return None


def find_body_props(lines, divider, verbose=False):
    # Search for all page body properties
    dv_prop = ""
    for index, line in enumerate(lines):
        if res := re.search(r"[a-zA-Z0-9-_[(]+::\s{1}.+", line):
            dv_prop = res.group().split(":: ")
            dv_prop = dv_prop[0]
            if verbose:
                print(f"Found body property: {dv_prop} on line {line}")
            move_inline_prop(lines, index, dv_prop, divider, verbose)


def find_prop(lines, search_str, divider, verbose=False):
    index_of_source = 0
    # Check existing YAML if not empty
    if divider > 1:
        index_of_source = find_linenum(
            lines, format_prop(search_str), 1, divider, verbose
        )
    # Search page body if not in YAML
    if not index_of_source:
        search_str = format_prop(search_str, True)
        index_of_source = find_linenum(lines, search_str, divider, 0, verbose)

    return index_of_source


def move_prop(lines, line_index, prop_name, divider, verbose=False):
    if verbose:
        print(f"Moving: {lines[line_index]}")
    line = lines.pop(line_index)
    line = clean_prop(line, prop_name)
    if check_for_multi_line(line):
        line = inline_to_multi_line(line)
    lines.insert(divider, line)


# TODO combine the move prop fns
def move_inline_prop(lines, line_index, prop_name, divider, verbose=False):
    if verbose:
        print(f"Moving: {lines[line_index]}")
    line = lines.pop(line_index)
    line = clean_prop(line, prop_name, True)
    lines.insert(divider, line)


def remove_prop(lines, line_index, verbose=False):
    if verbose:
        print(f"Removing: {lines[line_index]}")
    lines.pop(line_index)


def clean_prop(line, prop_name, inline=False):
    # Remove everything preceding the property name
    start = line.find(prop_name)
    line = line[start:]
    # Strip whitespace
    line = line.strip()
    # Handle inline props
    if inline:
        line = clean_inline_prop(line, prop_name)
    # Reformat attribute name
    line = line.replace("::", ":")
    line = line[0].lower() + line[1:]
    # Remove blockref at end
    found = line.find("^")
    if found > 0:
        line = line[:found]
    # Quote double brackets
    line = line.replace("[[", '"[[')
    line = line.replace("]]", ']]"')
    line = line + "\n"
    return line


def clean_inline_prop(line, prop_name):
    search_char = ""
    if prop_name[0] == "[":
        search_char = "]"
    if prop_name[0] == "(":
        search_char = ")"
    if search_char:
        end_char = line.rfind(search_char)
        if end_char != -1:
            line = line[1 : end_char - 1]
    return line


def format_prop(prop_name, inline=False):
    prop_name = prop_name + ":"
    if inline:
        prop_name = prop_name + ":"
    return prop_name


def check_for_multi_line(line):
    """Check the input string to determine if it should be converted from a comma delineated single line to a multi-line

    Args:
        line (str): input text string terminating in \n

    Returns:
        boolean: is this a multi-line property?
    """
    if "," not in line:
        return False
    if re.search(r",[^\[]+\]\]", line):  # ,\s+\[\[
        return False
    return True


def inline_to_multi_line(line):
    line = line.split(":", 1)
    output = line[0].strip() + ":"
    elements = line[1].split(",")
    for element in elements:
        if keyword := element.strip():
            output += "\n  - " + keyword
    output = output + "\n"
    return output


def main(args):
    # Access the values of the command-line arguments
    file_name = args.file
    all_inline = args.all
    verbose_mode = args.verbose
    if args.test:
        verbose_mode = True
    move_props = args.move
    remove_props = args.remove

    file_lines = []
    file_lines = read_file(file_name)
    # Abort if file not found
    if not file_lines:
        exit()

    # Find YAML end marker
    yaml_line = 0
    yaml_line = find_linenum(file_lines, "---", 1)
    if not yaml_line:
        file_lines.insert(0, "---\n---\n")
        yaml_line = 1

    # Find & move properties
    line_num = 0
    if all_inline:
        find_body_props(file_lines, yaml_line, verbose_mode)

    if move_props:
        for i in range(len(move_props) - 1, -1, -1):
            if line_num := find_prop(
                file_lines, move_props[i], yaml_line, verbose_mode
            ):
                move_prop(file_lines, line_num, move_props[i], yaml_line, verbose_mode)

    # Remove old properties
    if remove_props:
        for tag in remove_props:
            if line_num := find_prop(file_lines, tag, yaml_line, verbose_mode):
                remove_prop(file_lines, line_num, verbose_mode)

    # Write out changes
    if args.test:
        test_write(file_lines)
    if args.write:
        write_file(file_name, file_lines, verbose_mode)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="A simple script to manipulate properties in Obsidian files."
    )

    # Add command-line flags
    parser.add_argument("-f", "--file", help="Specify a file name", required=True)
    parser.add_argument(
        "-a", "--all", action="store_true", help="All inline properties"
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose mode"
    )
    parser.add_argument("-t", "--test", action="store_true", help="Enable test mode")
    parser.add_argument("-w", "--write", action="store_true", help="Enable write mode")
    parser.add_argument(
        "-mv",
        "--move",
        nargs="+",
        help="Properties to move separated by spaces.\nThese will be "
        "placed at the end of existing properties in order listed",
    )
    parser.add_argument(
        "-rm", "--remove", nargs="+", help="Properties to remove separated by spaces"
    )

    # Parse the command-line arguments
    try:
        args = parser.parse_args()
    except:
        print("No arguments specified. Use -h to see more information")
    else:
        main(args)

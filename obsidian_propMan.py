"""A simple script to manipulate properties in Obsidian notes.

This script allows you to move inline/body properties into the YAML frontmatter
or delete properties from a note. It can operate on a single file or an entire directory.

Usage example:
    Single file:
        python obsidian_propMan.py -f path/to/file.md [options]
    Directory:
        python obsidian_propMan.py -d path/to/directory [options]

Options:
    -f, --file       Specify input file path
    -d, --directory  Specify directory containing markdown files to process
    -a, --all        Move all inline properties to YAML frontmatter
    -mv [PROPS]      Move specific properties to YAML frontmatter
    -rm [PROPS]      Remove specific properties
    -p, --preview   Preview changes without writing to file
    -w, --write     Write changes to file
    -v, --verbose   Enable verbose output

Examples:
    # Move all inline properties in a file:
    python obsidian_propMan.py -f note.md -a -w

    # Move specific properties from all files in a directory:
    python obsidian_propMan.py -d ./notes -mv status tags -w

    # Remove properties from a file:
    python obsidian_propMan.py -f note.md -rm oldtag -w
"""
import argparse
import re
import os


def get_files_from_directory(directory_path):
    """Get all markdown files from the specified directory

    Args:
        directory_path (string): path to the directory to process

    Returns:
        list: list of full file paths for all markdown files in the directory
    """
    files = []
    try:
        for file in os.listdir(directory_path):
            if file.endswith('.md'):  # Only process markdown files
                full_path = os.path.join(directory_path, file)
                files.append(full_path)
        return files
    except Exception as e:
        print(f"Error reading directory: {e}")
        return []


def read_file(file_path):
    """Open a specified file, read the contents, and return them using python built-in methods

    Args:
        file_path (string): full path to the file including file name and extension

    Returns:
        list with each line (separated by \n) as an element
    """
    try:
        # Open the file in read mode
        with open(file_path, "r") as file:
            return file.read().splitlines()
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
    """Find the line number containing a target string within specified line range.

    Args:
        lines (list): List of strings to search through
        target_string (str): String to search for
        start (int, optional): Line number to start search from. Defaults to 0.
        stop (int, optional): Line number to end search at. Defaults to 0 (end of file).
        verbose (bool, optional): Whether to print verbose output. Defaults to False.

    Returns:
        int or None: Line number where target was found (0-based), or None if not found
    """
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
    """Search for and process all page body properties in given lines.

    Args:
        lines (list): List of text lines to search through
        divider (int): Line number of YAML frontmatter divider
        verbose (bool, optional): Whether to print verbose output. Defaults to False.
    """
    dv_prop = ""
    for index, line in enumerate(lines):
        if res := re.search(r"[a-zA-Z0-9-_[(]+::\s{1}.+", line):
            dv_prop = res.group().split(":: ")
            dv_prop = dv_prop[0]
            if verbose:
                print(f"Found body property: {dv_prop} on line {line}")
            move_inline_prop(lines, index, dv_prop, divider, verbose)


def find_prop(lines, search_str, divider, verbose=False):
    """Find a specific property in either YAML frontmatter or page body.

    Args:
        lines (list): List of text lines to search through
        search_str (str): Property name to search for
        divider (int): Line number of YAML frontmatter divider
        verbose (bool, optional): Whether to print verbose output. Defaults to False.

    Returns:
        int: Line number where property was found, or 0 if not found
    """
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
    """Move a property from its current location to the YAML frontmatter.

    Args:
        lines (list): List of text lines
        line_index (int): Index of line containing property to move
        prop_name (str): Name of property to move
        divider (int): Line number of YAML frontmatter divider
        verbose (bool, optional): Whether to print verbose output. Defaults to False.
    """
    if verbose:
        print(f"Moving: {lines[line_index]}")
    line = lines.pop(line_index)
    line = clean_prop(line, prop_name)
    if check_for_multi_line(line):
        line = inline_to_multi_line(line)
    lines.insert(divider, line)


def move_inline_prop(lines, line_index, prop_name, divider, verbose=False):
    """Move an inline property from its current location to the YAML frontmatter.

    Args:
        lines (list): List of text lines
        line_index (int): Index of line containing property to move
        prop_name (str): Name of property to move
        divider (int): Line number of YAML frontmatter divider
        verbose (bool, optional): Whether to print verbose output. Defaults to False.
    """
    if verbose:
        print(f"Moving: {lines[line_index]}")
    line = lines.pop(line_index)
    line = clean_prop(line, prop_name, True)
    lines.insert(divider, line)


def remove_prop(lines, line_index, verbose=False):
    """Remove a property from the file.

    Args:
        lines (list): List of text lines
        line_index (int): Index of line containing property to remove
        verbose (bool, optional): Whether to print verbose output. Defaults to False.
    """
    if verbose:
        print(f"Removing: {lines[line_index]}")
    lines.pop(line_index)


def clean_prop(line, prop_name, inline=False):
    """Cleans and formats a property line for YAML frontmatter.

    Args:
        line: String containing the full property line to clean
        prop_name: String name of the property being cleaned
        inline: Boolean indicating if this is an inline property

    Returns:
        String containing the cleaned and reformatted property line
    """
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
    """Cleans inline property syntax from a property line.

    Args:
        line: String containing the inline property line to clean
        prop_name: String name of the property being cleaned

    Returns:
        String with inline property syntax removed
    """
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
    """Formats a property name with appropriate colon syntax.

    Args:
        prop_name: String name of property to format
        inline: Boolean indicating if this is an inline property

    Returns:
        String containing formatted property name
    """
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
    """Converts a comma-separated single line property to multi-line YAML format.

    Args:
        line: A string containing a comma-separated property value.
            Expected format: "property_name: value1, value2, value3"

    Returns:
        A string containing the property in multi-line YAML list format:
            property_name:
              - value1
              - value2
              - value3

    """
    line = line.split(":", 1)
    output = line[0].strip() + ":"
    elements = line[1].split(",")
    for element in elements:
        if keyword := element.strip():
            output += "\n  - " + keyword
    output = output + "\n"
    return output


def main(args):
    """Main function to process Obsidian markdown files and manipulate their properties.

    Processes command line arguments to move or remove properties in markdown files.
    Can operate on a single file or directory of files. Properties can be moved from
    inline/body to YAML frontmatter or removed entirely.

    Args:
        args: Command line arguments parsed by argparse containing:
            file: Path to single markdown file to process
            directory: Path to directory of markdown files to process
            all: Boolean to move all inline properties
            verbose: Boolean to enable verbose output
            preview: Boolean to preview changes without writing
            write: Boolean to write changes to files
            move: List of property names to move to frontmatter
            remove: List of property names to remove

    Returns:
        None
    """
    # Access the values of the command-line arguments
    file_name = args.file
    directory = args.directory
    all_inline = args.all
    verbose_mode = args.verbose
    # Set preview mode if write mode is not enabled
    preview_mode = args.preview or not args.write
    if preview_mode:
        verbose_mode = True
    move_props = args.move
    remove_props = args.remove

    # Get list of files to process
    files_to_process = []
    if file_name:
        files_to_process.append(file_name)
    elif directory:
        files_to_process = get_files_from_directory(directory)
        if not files_to_process:
            print(f"No markdown files found in directory: {directory}")
            exit()

    # Process each file
    for file_path in files_to_process:
        if verbose_mode:
            print(f"\nProcessing file: {file_path}")

        file_lines = read_file(file_path)
        # Skip to next file if current file not found
        if not file_lines:
            continue

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
                if line_num := find_prop(file_lines, move_props[i], yaml_line, verbose_mode):
                    move_prop(file_lines, line_num, move_props[i], yaml_line, verbose_mode)

        # Remove old properties
        if remove_props:
            for tag in remove_props:
                if line_num := find_prop(file_lines, tag, yaml_line, verbose_mode):
                    remove_prop(file_lines, line_num, verbose_mode)

        # Write out changes
        if preview_mode:
            print(f"\nPreview for {file_path}:")
            test_write(file_lines)
        if args.write:
            write_file(file_path, file_lines, verbose_mode)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="A simple script to manipulate properties in Obsidian files."
    )

    # Add command-line flags
    file_group = parser.add_mutually_exclusive_group(required=True)
    file_group.add_argument("-f", "--file", help="Specify a file name")
    file_group.add_argument("-d", "--directory", help="Specify a directory to process all markdown files")
    parser.add_argument(
        "-a", "--all", action="store_true", help="All inline properties"
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose mode"
    )
    parser.add_argument("-p", "--preview", action="store_true", help="Enable preview mode")
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

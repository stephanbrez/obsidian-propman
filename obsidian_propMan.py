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

# Pre-compile all regex patterns used in the script
PATTERNS = {
    'DV_PROP': re.compile(r'(?:[\[(].+?[\])]|(?:^|\s*[-]|\s*>)\s*[a-zA-Z0-9-_]+::\s.+)'),
    'MULTI_LINE': re.compile(r",[^\[]+\]\]"),
    'BLOCKREF': re.compile(r"\^[a-zA-Z0-9-]+"),
    'DOUBLE_BRACKETS': re.compile(r"\[\[.*?\]\]"),
    'COMMA_SPLIT': re.compile(r',\s*'),  # For splitting comma-separated values
    'PROPERTY_VALUE': re.compile(r':\s*(.+)'),  # For extracting property values
    'YAML_PROPERTY': re.compile(r'^([^:]+):\s*(.*)$'),  # For parsing YAML properties
}

def get_files_from_directory(directory_path):
    """Get all markdown files from the specified directory

    Args:
        directory_path (string): path to the directory to process

    Returns:
        list: list of full file paths for all markdown files in the directory
    """
    try:
        return [os.path.join(directory_path, f)
                for f in os.listdir(directory_path)
                if f.endswith('.md')]
    except Exception as e:
        print(f"Error reading directory: {e}")
        return []


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
    # Check YAML and body in one pass
    yaml_prop = format_prop(search_str)
    body_prop = format_prop(search_str, True)

    for i, line in enumerate(lines):
        if (i < divider and yaml_prop in line) or \
           (i >= divider and body_prop in line):
            return i
    return 0

def batch_process_props(lines, divider, move_props=None, remove_props=None, all_inline=False, verbose=False):
    """Batch process all property changes before modifying the file.

    Args:
        lines (list): File lines to process
        divider (int): YAML frontmatter divider line number
        move_props (list): Properties to move to frontmatter
        remove_props (list): Properties to remove
        all_inline (bool): Whether to move all inline properties
        verbose (bool): Enable verbose output

    Returns:
        list: Modified lines with all changes applied
    """
    # Store changes as (operation, line_index, new_content)
    # operation: 'move' or 'remove'
    changes = []

    # Process all inline properties if requested
    if all_inline:
        for index, line in enumerate(lines):
            if res := PATTERNS['DV_PROP'].search(line):
                match = res.group(0)
                if match.startswith('[') or match.startswith('('):
                    # Handle bracketed property
                    inner_content = match[1:-1]
                else:
                    # Handle line-start/after-character property
                    # Remove leading characters if present
                    inner_content = match.lstrip('- ').lstrip('> ')

                # Split at :: to separate property name and value
                prop_name, value = inner_content.split(":: ", 1)
                if verbose:
                    print(f"Found inline property: {prop_name} on line {index}")
                new_content = inline_to_yaml(inner_content)
                changes.append(('move', index, new_content))

    # Process specific properties to move
    if move_props:
        for prop in move_props:
            if line_num := find_prop(lines, prop, divider, verbose):
                new_content = clean_prop(lines[line_num], prop)
                if check_for_multi_line(new_content):
                    new_content = inline_to_multi_line(new_content)
                changes.append(('move', line_num, new_content))

    # Process properties to remove
    if remove_props:
        for prop in remove_props:
            if line_num := find_prop(lines, prop, divider, verbose):
                changes.append(('remove', line_num, None))

    # Apply all changes in reverse order (to maintain correct line numbers)
    for operation, line_num, content in sorted(changes, key=lambda x: x[1], reverse=True):
        if operation == 'remove':
            if verbose:
                print(f"Removing line {line_num}: {lines[line_num]}")
            lines.pop(line_num)
        else:  # move
            if verbose:
                print(f"Moving line {line_num} to YAML frontmatter")
            lines.pop(line_num)
            lines.insert(divider, content)
    return lines

def clean_prop(line, prop_name):
    """Cleans and formats a text line  for YAML frontmatter.
    Sets everything from "::" to the end of the line as the property value.
    Removes blockrefs and quotes double brackets.

    Args:
        line: String containing the full property line to clean
        prop_name: String name of the property being cleaned
        inline: Boolean indicating if this is an inline property

    Returns:
        String containing the cleaned and reformatted property line
    """
    # Find property name and end positions
    start = line.find(prop_name)
    end = line.rfind("^")
    if end < 0:
        end = len(line)

    # Extract and clean the property value portion
    line = line[start:end].strip()

    # Single string operation for formatting
    line = inline_to_yaml(line)

    return line

def inline_to_yaml(line):
  return f"{line[0].lower()}{line[1:].replace('::', ':').replace('[[', '"[[').replace(']]', ']]"')}\n"

def format_prop(prop_name, inline=False):
    """Formats a property name with appropriate colon syntax.
    Single colon for YAML frontmatter, double colon for inline properties.

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
    if PATTERNS['MULTI_LINE'].search(line):  # ,\s+\[\[
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
    # Use regex to split property name and value
    if match := PATTERNS['YAML_PROPERTY'].match(line):
        prop_name, values = match.groups()
        output = prop_name.strip() + ":"

        # Split values using regex
        elements = values.split(",")

        for element in elements:
            if keyword := element.strip():
                output += f"\n  - {keyword}"

        return output + "\n"


def main(args):
    """Main function to process Obsidian markdown files and manipulate their properties.

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

        # Process all property changes in batch
        file_lines = batch_process_props(
            file_lines,
            yaml_line,
            move_props=args.move,
            remove_props=args.remove,
            all_inline=args.all,
            verbose=verbose_mode
        )

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

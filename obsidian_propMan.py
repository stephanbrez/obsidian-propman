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
    'DV_PROP': re.compile(r'(?:[\[(][a-zA-Z0-9-_]+::\s.+?[\])]|(?:^|\s*[-]|\s*>)\s*[a-zA-Z0-9-_]+::\s.+)'),
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

def export_debug_state(lines, filename_suffix):
    """Export current state to a debug file"""
    debug_filename = f"debug_state_{filename_suffix}.txt"
    with open(debug_filename, "w") as f:
        for i, line in enumerate(lines):
            f.write(f"{i}: {line}\n")
    return debug_filename

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
    yaml_prop = fix_colon(search_str)
    body_prop = fix_colon(search_str, True)

    for i, line in enumerate(lines):
        if (i < divider and yaml_prop in line) or \
           (i >= divider and body_prop in line):
            return i
    return 0

def batch_process_props(lines, divider, move_props=None, remove_props=None, all_inline=False, verbose=False):
    """Process properties in distinct phases to maintain correct ordering.

    Processing order:
    1. Remove specified properties
    2. Move inline properties (maintaining document order)
    3. Move specified properties (maintaining user-specified order) - allows reordering of any property

    Args:
        lines (list): File lines to process
        divider (int): YAML frontmatter divider line number
        move_props (list): Properties to move to frontmatter in specified order
        remove_props (list): Properties to remove
        all_inline (bool): Whether to move all inline properties
        verbose (bool): Enable verbose output

    Returns:
        list: Modified lines with all changes applied
    """
    # Create a working copy of lines
    modified_lines = lines.copy()

    # Initial line count
    if verbose:
        initial_count = len(modified_lines)
        print(f"\nInitial line count: {initial_count}")

    # Track line changes
    lines_removed = 0
    multi_line_expansions = 0

    # Phase 1: Remove specified properties
    if remove_props:
        if verbose:
            print("\nPhase 1: Removing properties")
        for prop in remove_props:
            if line_num := find_prop(modified_lines, prop, divider, verbose):
                if verbose:
                    print(f"Marking for removal: {modified_lines[line_num]}")
                modified_lines.pop(index)
                lines_removed += 1

    # Phase 2: Move inline properties in document order
    if all_inline:
        if verbose:
            print("\nPhase 2: Moving inline properties")
        indices_to_remove = []
        yaml_insertions = []

        # First pass: collect all inline properties
        for index, line in enumerate(modified_lines):
            if res := PATTERNS['DV_PROP'].search(line):
                match = res.group(0)

                # Handle bracketed/parenthesized inline properties
                if match.startswith('[') or match.startswith('('):
                    inner_content = match[1:-1]
                    content = inline_to_yaml(inner_content)
                    new_line = line.replace(match, '').strip()
                    if new_line:
                        modified_lines[index] = new_line + '\n'
                    else:
                        indices_to_remove.append(index)
                else:
                    # Handle regular inline properties
                    inner_content = match.lstrip('- ').lstrip('> ')
                    content = clean_prop(inner_content)
                    indices_to_remove.append(index)

                # Process the property content
                if check_for_multi_line(content):
                    content = inline_to_multi_line(content)
                    # Count additional lines created by multi-line conversion
                    multi_line_expansions += content.count('\n') - 1
                yaml_insertions.append(content)

                if verbose:
                    print(f"Found inline property on line {index}: {content}")

        # Remove empty lines in reverse order
        for index in sorted(indices_to_remove, reverse=True):
            modified_lines.pop(index)
            lines_removed += 1

        # Add collected properties to YAML in original order
        for content in reversed(yaml_insertions):
            modified_lines.insert(divider, content)

    # Phase 3: Move specified properties in user-defined order
    if move_props:
        if verbose:
            print("\nPhase 3: Moving specified properties")
        for prop in move_props:
            # Find and remove the property from its current location
            if line_num := find_prop(modified_lines, prop, divider, verbose):
                content = clean_prop(modified_lines[line_num], prop)
                if check_for_multi_line(content):
                    content = inline_to_multi_line(content)
                    # Count additional lines created by multi-line conversion
                    multi_line_expansions += content.count('\n') - 1
                if verbose:
                    print(f"Moving to YAML: {content}")
                modified_lines.pop(line_num)
                modified_lines.insert(divider, content)

    # Final line count and validation
    if verbose:
        final_count = len(modified_lines)
        expected_count = initial_count - lines_removed + multi_line_expansions
        print(f"\nLine count summary:")
        print(f"Initial lines: {initial_count}")
        print(f"Lines removed: {lines_removed}")
        print(f"Additional lines from multi-line conversions: {multi_line_expansions}")
        print(f"Expected final count: {expected_count}")
        print(f"Actual final count: {final_count}")
        if expected_count != final_count:
              print(f"WARNING: Line count mismatch! Expected {expected_count} but got {final_count}")
              debug_file = export_debug_state(modified_lines, "mismatch")
              print(f"\nDebug state exported to: {debug_file}")

    return modified_lines

def clean_prop(line, prop_name=None):
    """Cleans and formats a text line  for YAML frontmatter.
    Sets everything from "::" to the end of the line as the property value.
    Removes everything before the property name and all blockrefs
    Adds quotes to double brackets to maintain wiki links.

    Args:
        line: String containing the full property line to clean
        prop_name: String name of the property being cleaned
        inline: Boolean indicating if this is an inline property

    Returns:
        String containing the cleaned and reformatted property line
    """
    # Find property name and end positions
    if prop_name:
      start = line.find(prop_name)
    else:
      start = 0
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

def fix_colon(prop_name, inline=False):
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

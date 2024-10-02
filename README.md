# obsidian-propman

Manage Obsidian properties without pesky GUIs

## Why?

It's really hard (sorta impossible) to bulk edit Dataview property fields in the body of Obsidian notes--markdown documents. You can move them up into the YAML frontmatter to make use of the Obsidian "file properties" functionality, but that creates a few more painful issues:

- You have to manually edit _each file individually_ to move (copy/paste) and reformat (convert to YAML) Dataview properties **one by one** into the frontmatter.
- Obsidian doesn't give you functionality to remove or reorder a property for multiple files at once.

## What?

Obsidian PropMan is a python tool that enables you to make changes to multiple files quickly and easily (if you have python setup) from the command line.

### Features

- _Move all or only specific Dataview properties into front matter_: no more hunting around for properties and manually copy pasting...save time and energy for **creating, not maintaining** more notes.
- _Delete a YAML or Dataview property from all files_: get rid a property that's redundant or no longer needed to reduce clutter and keep Obsidian snappy.
- _Reorder front matter properties_: place fields in the order of your choosing to create visual consistency for easier reading across all your notes.
- _Preview edits_: see what changes will be made to your notes **before** saving them so that you don't accidentally delete things.
- _Verbose mode_: detailed status messages to find out which properties are being modified so there are no surprises.

## How

Run the script `python3 obsidian-propman.py` with the following flags:

- `-f`, `--file` Specify a file name. (Required)
- `-a`, `--all` All inline properties. Move all Dataview properties from the note body to front matter.
- `-mv`, `--move` Properties to move separated by spaces. These will be placed at the end of existing properties in order listed.
- `-rm`, `--remove` Properties to remove separated by spaces.
- `-v`, `--verbose` Enable verbose mode.
- `-t`, `--test` Enable test mode. Print the edited contents of the file **only to screen**.
- `-w`, `--write` Enable write mode. Save the modifications to the file, by **overwriting existing content**.

For example to view which changes would be made to the "test" note by moving dataview properties "keywords" and "author" to the front matter, and deleting the "date_last_modified" property:

```
python3 obsidian-propman.py -f /my/vault/notes/test.md -mv keywords author -rm date_last_modified -v
```

To see what the note would look like after making those same edits:

```
python3 obsidian-propman.py -f /my/vault/notes/test.md -mv keywords author -rm date_last_modified -v -t
```

To save those same edits without seeing them (😮):

```
python3 obsidian-propman.py -f /my/vault/notes/test.md -mv keywords author -rm date_last_modified -w
```

### Directories

To operate on all markdown files in a given directory pass your python command
to a `find` command with the specially formatted `-f` flag:

```bash
find <target_dir> -type f -name '*.md' - exec bash -c "<your python command> -f \"{}\"" \;
```

So using the example above, you'd run:

```bash
find /my/vault/notes -type f -name '*.md' -exec bash -c "python3 obsidian-propman.py -t -mv author keywords -rm date_last_modified -w -f \"{}\"" \;
```

This is a bit hacky but works until a directory flag is implemented.

## Coming Soon (or maybe in awhile)

- Directory flag to operate on all markdown files in a given directory.
- Rename Dataview properties

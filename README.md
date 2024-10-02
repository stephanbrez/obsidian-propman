# obsidian-propman
Manage Obsidian properties without pesky GUIs

## Why?
It's really hard (sorta impossible) to bulk edit Dataview property fields in the body of Obsidian notes--markdown documents. You can move them up into the YAML frontmatter to make use of the Obsidian "file properties" functionality, but that creates a few more painful issues:
- You have to manually edit *each file individually* to move (copy/paste) and reformat (convert to YAML) Dataview properties **one by one** into the frontmatter. 
- Obsidian doesn't give you functionality to 

## What?
Obsidian PropMan is a python tool that enables you to make changes to multiple files quickly and easily (if you have python setup) from the command line.

### Features*
- Move all or only specific dataview properties into frontmatter: no more hunting around for properties and manually copy pasting...save time and energy for **creating, not maintaining** more notes.
- Delete a YAML or Dataview property from all files: get rid a property that's redundant or no longer needed to reduce clutter and keep Obsidian snappy.
- Reorder frontmatter properties: place fields in the order of your choosing to create visual consistency for easier reading across all your notes.
- Preview edits: see what changes will be made to your notes **before** saving them so that you don't accidentally delete things.
- Verbose mode: detailed status messages to find out which properties are being modified so there are no surprises.

## How
Run the script `python3 obsidian-propman.py` with the following flags:
- `-f`, `--file`         Specify a file name. (Required)
- `-a`, `--all`          All inline properties. Move all Dataview properties from the note body to frontmatter.
- `-mv`, `--move`        Propreties to move separated by spaces. These will be placed at the end of existing properties in order listed.
- `-rm`, `--remove`      Properties to remove separated by spaces.
- `-v`, `--verbose`      Enable verbose mode.
- `-t`, `--test`         Enable test mode. Print the edited contents of the file **only to screen**.
- `-w`, `--write`        Enable write mode. Save the modifications to the file, by **overwriting existing content**.

For example to view which hanges would be made to the "test" note by moving dataview properties "keywords" and "author" to the frontmatter, and deleting the "date_last_modified" property:
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

## Coming Soon (or maybe in awhile)
- Rename Dataview properties

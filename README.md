# budgettool

A simple command line tool to keep track of expenses and earnings.

I made this because I like to code and want to improve. I can't see this being useful to anyone else but am now writing it as though it will be. I wanted a straightforward CLI to keep track of my finances. All entries are stored in CSV and thus are easily reusable. The interface is supposed to be designed for people who don't use CLIs (e.g. my wife). This makes it easy-ish to use but does limit the functionality. It's pretty regressive software design since it has nothing to do with the internet, but that's what I'm shooting for. If by chance you read my code, feedback would be very much appreciated.

## To Do

- Help command
- Incorporate graphing with matplotlib
    - bar graph categories for year and month
    - monthly income and expenses over year
- Goals for categories; sub categories?
- Config command
    - Prevent keywords from being used as users or categories
- Warn when current year is not active year
- Preset expenses and bills
- Get entry ID more efficiently
- Show hidden entries, ability to permanently delete
- Summarize command
- Separate earner and note for edit command
- Add more dummy data
- Implement undo and redo?
- Wrap input function for shell, so users can get always help or quit; takes context param(s)
- User attached to expenses as well (can be blank)
- List multiple categories

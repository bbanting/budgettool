# budgettool

A simple command line tool to keep track of expenses and earnings.

I made this because I like to code and want to improve. I can't see this being useful to anyone else but am now writing it as though it will be. I wanted a straightforward CLI to keep track of my finances. All entries are stored in CSV and thus are easily reusable. The interface is supposed to be designed for people who don't use CLIs (e.g. my wife). This makes it easy-ish to use but does limit the functionality. It's pretty regressive software design since it has nothing to do with the internet, but that's what I'm shooting for. If by chance you read my code, feedback would be very much appreciated.

## To Do

- [ ] Help command
- [ ] Incorporate graphing
    - bar graph categories for year and month
    - monthly income and expenses over year
    - Prevent keywords from being used as users or categories
- [ ] Warn when current year is not active year
- [ ] Preset expenses and bills (goals)
    - tags attached to goals 
        - any and all relationships
- [ ] Show hidden entries, ability to permanently delete
- [ ] Implement undo and redo?
- [ ] Wrap input function for shell, so users can get always help or quit; takes context param(s)
- [ ] Go back a step in adding an entry (or editing)
- [ ] Write tests
- [ ] List old months when no entries in latest month
- [ ] List n last entries (/n)
- [ ] Make summarize more insightful
- [ ] Search descriptions
- [ ] Calendar view
- [ ] Fix formatting in light of tags (remove tags from output?)
- [ ] Any and all relationships for search tags; negating
    - tag+tag tag !tag tag+!tag
    - ! and + are reserved and cant be used in tag names
- [ ] When tags are removed by user, put into "old_tags" if there are entries that reference it
- [ ] Watch dog or timeout for current year when changed from outside the shell
- [ ] Put records in records directory
- [x] return an args dictionary including the branch instead of a list
- [ ] Fix branch fallthrough behaviour and extra arguments problem
  - extra args should probably stop the command
  - Branch class with comparison operator overloading?
- [ ] Validate processed data dict before returning; make sure no duplicate keys

## Notes
- Remove ability to do one-off commands?
- Seems pretty tightly coupled as it is now.
  - Entry is tied to EntryList through global variable
  - EntryList is tied to Config through global variable
  - Can I make this better?
- Might be worth creating a common way to parse arguments that all commands can use
  - All command functions annotated with their keyword names
  - as well as argument sets (branches)
  - each argument has a validator, either standard or custom, and a name
  - a validator takes one argument and returns a value or raises an error
  - functions continue on the first branch to match
    - contain dict with arguments for that branch
    - irrelevant args are either removed or stored in 'args' key
- Parser solves some problems but still isn't really user friendly (namely branches)
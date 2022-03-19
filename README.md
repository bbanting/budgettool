# budgettool

A simple command line tool to keep track of expenses and earnings.

I made this because I like to code and want to improve. I can't see this being useful to anyone else but am now writing it as though it will be. I wanted a straightforward CLI to keep track of my finances. All entries are stored in CSV and thus are easily reusable. The interface is supposed to be designed for people who don't use CLIs (e.g. my wife). This makes it easy-ish to use but does limit the functionality. It's pretty regressive software design since it has nothing to do with the internet, but that's what I'm shooting for. If by chance you read my code, feedback would be very much appreciated.

## To Do

- [ ] Incorporate graphing
    - bar graph categories for year and month
    - monthly income and expenses over year
- [ ] Warn when current year is not active year
- [ ] Preset expenses and bills (goals)
    - tags attached to goals 
        - any and all relationships
- [ ] Go back a step in adding an entry (or editing)
- [ ] Write tests
- [ ] List old months when no entries in latest month
- [ ] Make summarize more insightful
- [ ] Search descriptions
- [ ] Calendar view
- [ ] Fix formatting in light of tags (remove tags from output?)
- [ ] Compound relationships for search tags; negating
    - tag+tag tag !tag tag+!tag
    - ! and + are reserved and cant be used in tag names
- [ ] Make a consistent API for display module
- [x] Truncate header and footer or give true line height
- [x] Allow for very large amount of page numbers
- [x] Solve problem of when to clear buffer
- [ ] Make min and max page height
- [ ] Make display select function

## Notes

- Seems pretty tightly coupled as it is now.
  - Entry is tied to EntryList through global variable
  - Can I make this better?
- An option would be to use sqlite and have the option to export to csv instead
- Possible to have no tags on entry?
- Is changing year necessary if an entry can easily be made with a different year?
- If there's no active year, how to differentiate ids between years when selecting for edit and delete?
  - hexadeciaml ids?
- A master records class; when iterated over, checks most recent years first
  - All records from all years are available but this way there isn't one ginormous file
  - Maybe use UserDict with custom `__iter__` and `__getitem__` methods?
- make command names case-insensitive?
- LineBuffer.true_height needs to account for numbering too
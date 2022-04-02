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
- [ ] Write tests
- [ ] Search descriptions
- [ ] Calendar view
- [ ] Fix formatting in light of tags (remove tags from output?)
- [ ] Compound relationships for search tags; negating
    - tag+tag tag !tag tag+!tag
    - ! and + are reserved and cant be used in tag names
- [ ] Change to sqlite3

## Notes

- Seems pretty tightly coupled as it is now.
  - Entry is tied to EntryList through global variable
  - Can I make this better?
- Is changing year necessary if an entry can easily be made with a different year?
- LineBuffer.true_height needs to account for numbering too
- Currently, if page numbers get too many digits long, they will overflow
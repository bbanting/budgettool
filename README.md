# budgettool

A simple command line tool to keep track of expenses and earnings.

I can't see this being useful to anyone else but am now writing it as though it will be. The interface is supposed to be designed for people who don't use CLIs (e.g. my wife). This makes it easy-ish to use but does limit the functionality. 

## To Do

- [ ] Incorporate graphing
    - bar graph categories for year and month
    - monthly income and expenses over year
- [ ] Write tests
- [ ] Search descriptions
- [ ] Export to csv
- [x] Maximum lengths for inputs

## Notes

- Currently, if page numbers get too many digits long, they will overflow
- Make command params dependant on others
- Replace target foreign key on entry with target_instance?
- Progress bars for targets?
- Project initializer?
- kelevsma config function?
- Screen types?
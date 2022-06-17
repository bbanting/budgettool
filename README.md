# budgettool

A simple command line tool to keep track of expenses and earnings.

I made this because I like to code and want to improve. I can't see this being useful to anyone else but am now writing it as though it will be. I wanted a straightforward CLI to keep track of my finances. All entries are stored in CSV and thus are easily reusable. The interface is supposed to be designed for people who don't use CLIs (e.g. my wife). This makes it easy-ish to use but does limit the functionality. It's pretty regressive software design since it has nothing to do with the internet, but that's what I'm shooting for. If by chance you read my code, feedback would be very much appreciated.

## To Do

- [ ] Incorporate graphing
    - bar graph categories for year and month
    - monthly income and expenses over year
- [ ] Write tests
- [ ] Search descriptions
- [ ] Make examples for all commands

## Notes

- Currently, if page numbers get too many digits long, they will overflow
- Make command params dependant on others
- Replace target foreign key on entry with target_instance?
- Progress bars for targets?
- Project initializer?
- kelevsma config function?
- db Table class?
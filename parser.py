### Small module for parsing arguments

from functools import wraps


class ParseError(Exception):
    pass


def command(*names: tuple[str]):
    def decorator(f):
        f.iscommand = True
        f.names = names
        @wraps(f)
        def wrapper(*args, **kwargs):
            return f(*args, **kwargs)
        return wrapper
    return decorator


def branch(name, *parsers: function):
    def decorator(f):
        f.branches.append({name: parsers})
        @wraps(f)
        def wrapper(*args, **kwargs):
            return f(*args, **kwargs)
        return wrapper
    return decorator


def process_input(args):
    """Process user input, route to appropriate function."""
    if not args:
        raise ParseError("No input given.")

    # Find the function
    command_name = args[0].lower()
    funcs = [x for x in globals() if hasattr(globals()[x], "iscommand")]
    if command_name not in funcs:
        raise ParseError("Command not found.")
    else:
        command = globals()[command_name]
    
    # Branches
    ### Does not currently work for a variable amount of arguments
    for branch in command.branches.values():
        if len(branch) != len(args[1:]):
            continue
        for parser in branch:
            for arg in args[1:]:
                if parser(arg) is not None:
                    break 
                    # set something with the parser
                    # remove the argument?
            else:
                break # go to next branch
        # If you're this far then this branch matches
        # use the data from that branch as argument to the command
    else:
        raise ParseError("No branches matched.")
    
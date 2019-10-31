import syrabond
import sys

sh = syrabond.Facility('sh', listen=False)


def switch(entity, name, command):
    if entity == 'switch':
        if command == 'toggle':
            sh.get_resource(name).toggle()
        if command == 'on':
            sh.get_resource(name).on()
        if command == 'off':
            sh.get_resource(name).off()


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Wrong arguments")
        print("Usage: syraponte.py <type_of_entity> <name> <command>")
        sys.exit(-1)
    entity = sys.argv[1]
    name = sys.argv[2]
    command = sys.argv[3]
    switch(entity, name, command)

import sys


def main():

    while True:
        sys.stdout.write("$ ")
        command=input()
        if command=="exit":
            break

        if command.startswith("echo "):
            print(command[5:])
            continue


        if command.startswith("type "):
            target=command[5:]
            if target in["echo","exit","type"]
                print(f"{target} is a shell builtin")
            else:
                print(f"{target}: not found")  


        print(f"{command}: command not found")
    pass


if __name__ == "__main__":
    main()

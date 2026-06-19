import sys,os,shutil,subprocess,shlex


def main():

    while True:
        sys.stdout.write("$ ")
        command=input()

        if not command.strip():
            continue

        try:
            command_parts = shlex.split(command)
        except ValueError:
            continue

        if not command_parts:
            continue

        program_name = command_parts[0]
        args = command_parts[1:]

        if program_name=="exit":
            break

        if program_name=="echo":
            print(" ".join(args))
            continue
        if program_name=="pwd":            
            print(os.getcwd())          
            continue

        if program_name=="cd":
            if not args:
                continue

            target=args[0]
            if target=="~":
                target=os.environ.get("HOME") #change dir to home
                
            try:
                os.chdir(target)

            except FileNotFoundError:
                print(f"cd: {target}: No such file or directory")
            continue



        if program_name=="type":
            if not args:
                continue
            target=args[0]
            if target in["echo","exit","type","pwd","cd"]:
                print(f"{target} is a shell builtin")
            else:
                path=shutil.which(target)
                if path:
                    print(f"{target} is {path}") 
                else:
                        print(f"{target}: not found")
            continue   

        
        
        path=shutil.which(program_name)

        if path:
            subprocess.run([program_name]+args)
        else:
            print(f"{command}: not found")


        


        # else:    
        #     print(f"{command}: command not found")
    pass


if __name__ == "__main__":
    main()

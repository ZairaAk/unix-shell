import sys,os,shutil,subprocess


def main():

    while True:
        sys.stdout.write("$ ")
        command=input()

        if command=="exit":
            break

        if command.startswith("echo "):
            print(command[5:])
            continue
        if command=="pwd":            
            print(os.getcwd())          
            continue

        if command.startswith("cd "):
            target=command[3:]
            if target=="~":
                target=os.environ.get("HOME") #change dir to home
                
            try:
                os.chdir(target)

            except FileNotFoundError:
                print(f"cd: {target}: No such file or directory")
            continue



        if command.startswith("type "):
            target=command[5:]
            if target in["echo","exit","type","pwd","cd"]:
                print(f"{target} is a shell builtin")
            else:
                path=shutil.which(target)
                if path:
                    print(f"{target} is {path}") 
                else:
                        print(f"{target}: not found")
            continue   

        
        command_parts=command.split()
        if not command_parts:
            continue
        program_name=command_parts[0]
        args=command_parts[1:]

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

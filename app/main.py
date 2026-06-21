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

        stdout_file=None
        stderr_file=None
        append_stdout= False

        if ">>" in command_parts or "1>>" in command_parts:
            operator=">>" if ">>" in command_parts else "1>>"
            idx = command_parts.index(operator)
            stdout_file = command_parts[idx + 1]
            command_parts = command_parts[:idx]
            append_stdout = True


        elif "2>" in command_parts:
            idx = command_parts.index("2>")
            stderr_file = command_parts[idx + 1]
            command_parts = command_parts[:idx]


        elif ">" in command_parts or "1>" in command_parts:
            operator = ">" if ">" in command_parts else "1>"
            idx=command_parts.index(operator)

            stdout_file=command_parts[idx+1]
            command_parts=command_parts[:idx]

        if not command_parts:
            continue

        program_name = command_parts[0]
        args = command_parts[1:]

        


        if program_name=="exit":
            break

        #echo doesn't produce an error.    
        if program_name=="echo":
            output=" ".join(args)

            if stdout_file:
                mode = "a" if append_stdout else "w"

                with open(stdout_file, mode) as f:
                    f.write(output + "\n")

            else:
                print(output)  

            # Create stderr file if 2> was used
            if stderr_file:
                open(stderr_file, "w").close()
    

            continue

        if program_name=="pwd":            
            output=os.getcwd()
            if stdout_file:
               mode = "a" if append_stdout else "w"
               with open(stdout_file, mode) as f:
                    f.write(output + "\n")
            else:
                print(output)
            
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
            if stderr_file:
                with open(stderr_file,"w") as f:
                    subprocess.run([program_name]+args, stderr=f)
            elif stdout_file:
                mode = "a" if append_stdout else "w"

                with open(stdout_file, mode) as f:
                    subprocess.run(
                        [program_name] + args,
                        stdout=f)
            else:
                subprocess.run([program_name]+args)
        else:
            print(f"{command}: not found")


        


        # else:    
        #     print(f"{command}: command not found")
    pass


if __name__ == "__main__":
    main()

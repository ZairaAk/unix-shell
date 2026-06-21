import sys
import os
import shutil
import subprocess
import shlex


def get_job_marker(job, jobs_list):
    if not jobs_list:
        return " "
    ordered = jobs_list
    current = ordered[-1]
    previous = ordered[-2] if len(ordered) >= 2 else None
    if job["id"] == current["id"]:
        return "+"
    elif previous is not None and job["id"] == previous["id"]:
        return "-"
    else:
        return " "


def format_job_line(job, marker, trailing_amp):
    status_str = job["status"].ljust(21) if marker == "+" else job["status"].ljust(24)
    suffix = " &" if trailing_amp else ""
    return f"[{job['id']}]{marker}  {status_str}{job['command']}{suffix}"


def reap_and_announce(jobs_list):
    still_running = []
    finished = []
    for job in jobs_list:
        if job["status"] == "Running":
            if job["process"].poll() is not None:
                job["status"] = "Done"
        if job["status"] == "Done":
            finished.append(job)
        else:
            still_running.append(job)

    for job in finished:
        marker = get_job_marker(job, jobs_list)
        print(format_job_line(job, marker, trailing_amp=False))

    return still_running


def main():
    jobs_list = []

    while True:
        jobs_list = reap_and_announce(jobs_list)

        sys.stdout.write("$ ")
        sys.stdout.flush()
        command = input()

        if not command.strip():
            continue

        try:
            command_parts = shlex.split(command)
        except ValueError:
            continue

        is_background = False
        if command_parts and command_parts[-1] == "&":
            is_background = True
            command_parts.pop()
        elif command_parts and command_parts[-1].endswith("&"):
            is_background = True
            command_parts[-1] = command_parts[-1][:-1]

        stdout_file = None
        stderr_file = None
        append_stdout = False
        append_stderr = False

        if "2>>" in command_parts:
            idx = command_parts.index("2>>")
            stderr_file = command_parts[idx + 1]
            command_parts = command_parts[:idx]
            append_stderr = True
        elif ">>" in command_parts or "1>>" in command_parts:
            operator = ">>" if ">>" in command_parts else "1>>"
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
            idx = command_parts.index(operator)
            stdout_file = command_parts[idx + 1]
            command_parts = command_parts[:idx]

        if not command_parts:
            continue

        program_name = command_parts[0]
        args = command_parts[1:]

        if program_name == "exit":
            break

        if program_name == "jobs":
            jobs_list = reap_and_announce(jobs_list)
            for job in jobs_list:
                marker = get_job_marker(job, jobs_list)
                print(format_job_line(job, marker, trailing_amp=True))
            continue

        if program_name == "echo":
            output = " ".join(args)
            if stdout_file:
                mode = "a" if append_stdout else "w"
                with open(stdout_file, mode) as f:
                    f.write(output + "\n")
            else:
                print(output)
            if stderr_file:
                open(stderr_file, "w").close()
            continue

        if program_name == "pwd":
            output = os.getcwd()
            if stdout_file:
                mode = "a" if append_stdout else "w"
                with open(stdout_file, mode) as f:
                    f.write(output + "\n")
            else:
                print(output)
            continue

        if program_name == "cd":
            if not args:
                continue
            target = args[0]
            if target == "~":
                target = os.environ.get("HOME")
            try:
                os.chdir(target)
            except FileNotFoundError:
                print(f"cd: {target}: No such file or directory")
            continue

        if program_name == "type":
            if not args:
                continue
            target = args[0]
            if target in ["echo", "exit", "type", "pwd", "cd", "jobs"]:
                print(f"{target} is a shell builtin")
            else:
                path = shutil.which(target)
                if path:
                    print(f"{target} is {path}")
                else:
                    print(f"{target}: not found")
            continue

        path = shutil.which(program_name)

        if path:
            f_out = open(stdout_file, "a" if append_stdout else "w") if stdout_file else None
            f_err = open(stderr_file, "a" if append_stderr else "w") if stderr_file else None
            try:
                if is_background:
                    p = subprocess.Popen([program_name] + args, stdout=f_out, stderr=f_err)
                    existing_ids = {j["id"] for j in jobs_list}
                    next_id = 1
                    while next_id in existing_ids:
                        next_id += 1
                    raw_cmd = f"{program_name} " + " ".join(args)
                    print(f"[{next_id}] {p.pid}")
                    jobs_list.append({
                        "id": next_id,
                        "process": p,
                        "command": raw_cmd.strip(),
                        "status": "Running",
                    })
                else:
                    subprocess.run([program_name] + args, stdout=f_out, stderr=f_err)
            finally:
                if not is_background:
                    if f_out:
                        f_out.close()
                    if f_err:
                        f_err.close()
        else:
            print(f"{command}: not found")


if __name__ == "__main__":
    main()
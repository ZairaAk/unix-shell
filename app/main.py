import sys
import os
import shutil
import subprocess
import shlex


def get_job_marker(job, jobs_list):
    """
    Determine the +/- marker for a job, bash-style:
    - '+' marks the current job: the most recently started job that is
      still in the table (Running or about to be reported Done).
    - '-' marks the previous job: the next-most-recent one after current.
    - Older jobs get a blank space instead of +/-.
    Order is based on the order jobs were added (insertion order in
    jobs_list reflects job id assignment order here).
    """
    if not jobs_list:
        return " "

    # Most recently added job is the last one with the highest id among
    # those still present - we use list order since jobs_list is built
    # in the order jobs were started, and ids are reused only after removal.
    ordered = jobs_list  # already in insertion order
    current = ordered[-1]
    previous = ordered[-2] if len(ordered) >= 2 else None

    if job["id"] == current["id"]:
        return "+"
    elif previous is not None and job["id"] == previous["id"]:
        return "-"
    else:
        return " "


def main():
    jobs_list = []

    while True:
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
            # Reap completed jobs *at the moment jobs is called*:
            # 1. poll() each running job without blocking
            # 2. print Done entries (no trailing &) for any that finished
            # 3. print Running entries (with trailing &) for any still going
            # 4. remove Done jobs from the table so they never show again
            #
            # Markers (+/-/space) are computed against the table as it
            # stood BEFORE removals for this call, so a job being reported
            # Done this round still gets its correct marker on its last
            # appearance.
            still_running = []
            for job in jobs_list:
                if job["status"] == "Running":
                    poll_result = job["process"].poll()
                    if poll_result is not None:
                        job["status"] = "Done"

                marker = get_job_marker(job, jobs_list)

                if marker == "+":
                    status_str = job["status"].ljust(21)
                else:
                    status_str = job["status"].ljust(24)

                if job["status"] == "Done":
                    print(f"[{job['id']}]{marker}  {status_str}{job['command']}")
                    # do not keep this job - it gets reaped (removed) now
                else:
                    print(f"[{job['id']}]{marker}  {status_str}{job['command']} &")
                    still_running.append(job)

            jobs_list = still_running
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
            f_out = (
                open(stdout_file, "a" if append_stdout else "w")
                if stdout_file
                else None
            )
            f_err = (
                open(stderr_file, "a" if append_stderr else "w")
                if stderr_file
                else None
            )

            try:
                if is_background:
                    p = subprocess.Popen(
                        [program_name] + args, stdout=f_out, stderr=f_err
                    )

                    existing_ids = {j["id"] for j in jobs_list}
                    next_id = 1
                    while next_id in existing_ids:
                        next_id += 1

                    raw_cmd = f"{program_name} " + " ".join(args)
                    print(f"[{next_id}] {p.pid}")

                    jobs_list.append(
                        {
                            "id": next_id,
                            "process": p,
                            "command": raw_cmd.strip(),
                            "status": "Running",
                        }
                    )
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
import sys
import os
import shutil
import subprocess
import shlex


def main():
    jobs_list = []

    while True:
        for job in jobs_list:
            if job["status"] == "Running":
                poll_result = job["process"].poll()
                if poll_result is not None:
                    job["status"] = "Done"

        jobs_list.sort(key=lambda x: x["id"])
        jobs_to_remove = []

        for job in jobs_list:
            if job["status"] == "Done":
                marker = " "
                if job == jobs_list[-1]:
                    marker = "+"
                elif len(jobs_list) > 1 and job == jobs_list[-2]:
                    marker = "-"
                
                status_str = "Done".ljust(21)
                print(f"[{job['id']}]{marker}  {status_str}{job['command']}")
                jobs_to_remove.append(job)

        for job in jobs_to_remove:
            jobs_list.remove(job)

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
            target_job_id = None
            if args:
                try:
                    target_job_id = int(args[0])
                except ValueError:
                    pass

            jobs_list.sort(key=lambda x: x["id"])
            jobs_to_remove = []

            for job in jobs_list:
                if target_job_id is not None and job["id"] != target_job_id:
                    continue
                
                if job["status"] == "Running":
                    if job["process"].poll() is not None:
                        job["status"] = "Done"

                marker = " "
                if job == jobs_list[-1]:
                    marker = "+"
                elif len(jobs_list)
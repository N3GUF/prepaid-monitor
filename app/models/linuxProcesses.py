import io
import subprocess


class LinuxProcess:
    def __init__(self, fields: list) -> None:
        self.userId = fields[0]
        self.processId = fields[1]
        self.parentProcessId = fields[2]
        self.cpu = fields[3]
        self.startTime = fields[4]
        self.terminal = fields[5]
        self.cpuTime = fields[6]
        self.command = ""

        for field in fields[7:]:
            self.command += field
            self.command += ""

    def __repr__(self):
        return (
            f"Process: {self.userId}, {self.processId}, {self.parentProcessId}, {self.cpu}, "
            f"{self.startTime}, {self.terminal}, {self.cpuTime}, {self.command}"
        )


class LinuxProcesses:
    def __init__(self, servers, user):
        self.processes = {}

        for server in servers:
            proc_list = []
            try:
                result = subprocess.Popen(
                    ["ssh", server, "ps", "-fu", user], stdout=subprocess.PIPE
                )

                if result.stdout is None:
                    continue

                for i, process in enumerate(
                    io.TextIOWrapper(result.stdout, encoding="utf-8")
                ):
                    if i == 0:
                        continue

                    proc_list.append(LinuxProcess(process.strip().split()))

            except OSError:
                pass

            self.processes[server] = proc_list

    def get(self):
        return self.processes

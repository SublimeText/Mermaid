import sublime
import sublime_plugin
import os
import sys
import subprocess
import time


class MermaidBuildCommand(sublime_plugin.WindowCommand):
    """Build command for Mermaid"""

    def handle_popen(self, handler):
        """Stream output from mermaid-cli"""
        err_collector = []
        while True:
            stdout = handler.stdout
            if not stdout:
                break
            output = stdout.readline()
            if not output:
                err = handler.stderr.readline()
                if not err:
                    break
                else:
                    err_collector.append(err.decode().rstrip())
            else:
                print(output.rstrip(), flush=True)
        if len(err_collector) > 0:
            sublime.error_message("Issue occurred when rendering Mermaid diagram:\n" + "\n".join(err_collector))
            return False
        return True

    def run(self):
        """Run the build and convert the Mermaid diagram."""
        view = self.window.active_view()
        if not view:
            return

        settings = sublime.load_settings("mermaid.sublime-settings")

        mmdc_cmd = settings.get("mmdc_location", "mmdc")
        build_settings = settings.get("build")
        # remove unused settings
        pruned_build_settings = {k: v for k, v in build_settings.items() if v}

        # set input file
        pruned_build_settings["input"] = view.file_name()

        # make output file
        output = os.path.splitext(view.file_name())
        outputFile = output[0]
        if "outputFormat" not in pruned_build_settings:
            outputFormat = "svg"
        else:
            outputFormat = pruned_build_settings["outputFormat"]

        outputFile = outputFile + "." + outputFormat
        pruned_build_settings["output"] = outputFile

        # handle the weird singleton flag
        pdfFit = None
        pdfFit = pruned_build_settings.pop("pdfFit")

        # create flags then flatten for Popen arg
        flags = [["--" + k, str(v)] for k, v in pruned_build_settings.items()]
        flattened_flags = [mmdc_cmd] + [x for i in flags for x in i]
        if outputFormat.lower() == "pdf" and pdfFit:
            flattened_flags += ["--pdfFit"]

        # run mmdc
        p = subprocess.Popen(flattened_flags, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # stream stdout and stderr
        success = self.handle_popen(p)

        if success:
            print("mmdc has finished generating. Rendered Mermaid is at " + outputFile)
            sublime.status_message("Build finished")

            will_open = settings.get("open_in_default_app_after_build", False)
            if will_open:
                if sys.platform == "darwin":
                    opener = "open"
                elif sys.platform == "linux":
                    opener = "xdg-open"
                elif sys.platform == "win32":
                    opener = "Invoke-Item"

                p = subprocess.Popen([opener, outputFile])
                self.handle_popen(p)

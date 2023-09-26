import os
import subprocess


class ScriptRunner:
    def __init__(self, folder_name='scripts'):
        self.folder_name = folder_name
        self.script_list = []

    def get_scripts(self):
        # Empty the list to avoid duplication
        self.script_list = []

        # Loop through the files in the folder
        for filename in os.listdir(self.folder_name):
            if (filename.endswith('.sh') or filename.endswith('.py')
                    or filename.endswith('.bat') or filename.endswith('.macro')):
                self.script_list.append(filename)

        return self.script_list

    def run_script(self, script_name):
        if script_name in self.script_list:
            # Run the script using subprocess
            script_path = os.path.join(self.folder_name, script_name)
            if script_name.endswith('.py'):
                subprocess.run(f"python3 {script_path}", shell=True)
            elif script_name.endswith('.bat'):
                subprocess.run(f"{script_path}", shell=True)
            elif script_name.endswith('.sh'):
                subprocess.run(f"bash {script_path}", shell=True)
            elif script_name.endswith('.macro'):
                self.run_macro(script_path)
        else:
            print(f"Script {script_name} not found.")

    def run_macro(self, script_path):
        with open(script_path, 'r') as f:
            for command in f:
                split_com = command.split(" ")
                num = 0
                if len(split_com) > 1:
                    num = split_com[1]

                com = split_com[0]

                if com.isalpha():
                    pass
                elif com == "shiftu":
                    pass  # Implementation for shiftu
                elif com == "shiftd":
                    pass  # Implementation for shiftd
                elif com == "ctrlu":
                    pass  # Implementation for ctrlu
                elif com == "ctrld":
                    pass  # Implementation for ctrld
                elif com == "altu":
                    pass  # Implementation for altu
                elif com == "altd":
                    pass  # Implementation for altd
                elif com == "delay":
                    pass  # Implementation for delay
                elif com == "escu":
                    pass  # Implementation for escu
                elif com == "escd":
                    pass  # Implementation for escd
                else:
                    print("Invalid command")


if __name__ == "__main__":
    # Create a ScriptRunner object
    runner = ScriptRunner()

    # Get all scripts in the 'scripts' folder
    print(runner.get_scripts())  # Output will be the list of script names

    runner.run_script('test.py')
    runner.run_script('test.bat')
    runner.run_script('test.sh')

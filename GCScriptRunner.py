import os
import subprocess
import pyautogui

# Todo: complete script runner macro support


class ScriptRunner:
    def __init__(self, folder_name='scripts'):
        self.folder_name = folder_name
        self.script_list = []
        self.get_scripts()

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
            script_path = f"{self.folder_name}/{script_name}"
            if script_name.endswith('.py'):
                subprocess.run(f"python3 {script_path}", shell=True)
            elif script_name.endswith('.macro'):
                self.run_macro(script_path)
            """elif script_name.endswith('.bat'):
                            subprocess.run(f"{script_path}", shell=True)"""
            """elif script_name.endswith('.sh'):
                            subprocess.run(f"bash {script_path}", shell=True)"""
        else:
            print(f"Script {script_name} not found.")

    def run_macro(self, script_path):
        with open(script_path, 'r') as f:
            for command in f:
                split_com = command.split(" ")
                num = 1
                if len(split_com) > 1:
                    num = split_com[1]

                com = split_com[0]
                if com[-1] == "\n":
                    com = com[:-1]

                for _ in range(num):
                    if com.isalpha() and len(com) == 1:
                        pyautogui.keyDown(com)
                    elif com == "delay":
                        pass  # Implementation for delay
                    elif com == "scrollu":
                        pyautogui.scroll(20)
                    elif com == "scrolld":
                        pyautogui.scroll(-20)
                    elif com[-1] == 'd':
                        pyautogui.keyDown(com[:-1])
                    elif com[-1] == 'u':
                        pyautogui.keyUp(com[:-1])
                    else:
                        pyautogui.press(com)
                        #print("Invalid command")


if __name__ == "__main__":
    # Create a ScriptRunner object
    runner = ScriptRunner()

    # Get all scripts in the 'scripts' folder
    print(runner.get_scripts())  # Output will be the list of script names

    runner.run_script('test.py')
    runner.run_script('test.bat')
    runner.run_script('test.sh')

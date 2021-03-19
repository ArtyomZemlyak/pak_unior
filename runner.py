# runner.py
"""Using to create exe filte to run sript main.py and launch all programm"""

import subprocess
import pathlib

pth = pathlib.Path(__file__).parent.absolute()

path = r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe"

com0 = r";C:\ProgramData\Anaconda3\shell\condabin\conda-hook.ps1"
com1 = r";conda activate pak_unior_test"
com2 = f';cd {pth}'
com3 = ';python main.py'

subprocess.Popen([path, com0, com1, com2, com3])

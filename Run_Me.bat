@echo off

:: Check if the environment already exists
if not exist env_python36 (
    :: Create the environment
    python -m venv env_python36
)

:: Activate the environment
call env_python36\Scripts\activate.bat


:: Check for required libraries and install if needed
pip install pyqt5 fbs || (
    echo Error installing libraries. Please check your internet connection and try again.
    pause
)

:: Change directory to the script location
cd src/main/python

:: Run your Python code
python main.py

:: Deactivate the environment
deactivate

:: Exit the batch file
exit /b 0

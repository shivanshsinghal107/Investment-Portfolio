# Student Investment Portfolio (SIP)
## How to run on local machine
- Open terminal/cmd and either download the zip file of repository or clone using below command(if git is installed):<br>
`git clone -b development --single-branch https://github.com/shivanshsinghal107/Investment-Portfolio.git`
- Extract the zip file(if downloaded directly) and go into the directory using cd:<br>
`cd DIRECTORY_NAME`
- Create a python virtual enviroment using below command(make sure python3.6+ is installed on your machine):<br>
  - For macOS or Linux:<br>
  `python3 -m venv env`
  - For Windows:<br>
  `py -m venv env`
- Activate the virtual enviroment:<br>
  - For macOS or Linux:<br>
  `source env/bin/activate`
  - For Windows:<br>
  `.\env\Scripts\activate`
- Install all the dependencies/libraries required:<br>
`pip3 install -r requirements.txt`
- After completing the installation, run the below command to initialize the database:<br>
`python3 data.py`
- Now run the application using below command:<br>
`flask run`

## Tech Stack
### Tools & Technologies
- Flask (Micro Web framework of python)
- Bootstrap (CSS framework)
- PostgreSQL (Relational Database Management System)

### Languages
- Python
- HTML
- CSS
- JavaScript

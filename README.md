This is a command-line tool that manages the student GitHub repositories of the Software Engineering class taught at EPFL.

## Class Data Model

Each student has access to two repositories: one for individual exams and a shared repository for team-based projects.  The tool takes care of configuring the right permissions for each student and repository, based on team membership information.

The student and team data reside in a [Google Sheets](https://docs.google.com/spreadsheets/) document, which the tool accesses through the Sheets API. Using a spreadsheet has several advantages:

  * It acts as a centralized place for student data, thus avoiding data duplication across different tools and use cases. The sheet acts as a lightweight central database that is both human and machine-readable.
  * The data can be annotated and expanded without affecting this tool's functionality.  For instance, cell formatting can be used to mark dropped-out students and additional sheets can be added for statistics, additional data, etc.

For convenience, we provide a [template spreadsheet][template] that you can use as a starting point for your own data.


## Prerequisites

The tool can be run from any machine that has access to the Internet and to EPFL's intranet.  Make sure that Python 2 is installed and available on the shell ``PATH``.


## Setting Up

Before using the tool, perform the following steps:

  1. Install the tool dependencies.  We provide a script that handles this automatically by creating a [Python virtualenv](http://docs.python-guide.org/en/latest/dev/virtualenvs/) in the ``venv/`` subdirectory relative to the repository root, which contains all script dependencies:

        $ ./setup_venv.sh

  2. Set up the GitHub organization that will hold the private student repositories.  You should create a free organization and then visit http://education.github.com/ to apply for free private repositories for your students.  You should ask for enough repositories to cover the exam and team repositories.  Create two GitHub teams in the organization: a Staff team and a Class team.  The former will be added to all repositories created by the tool, while the latter is used in case the staff decides to open the repositories to all students.  The names of the teams don't matter, but you should write down their numeric IDs, which you find in the team URLs in the web UI.

  3. Create the Google spreadsheet holding student and team information.  The simplest approach is to make a copy of the [template spreadsheet][template] and populate it with your student and team data.  Make sure to give the spreadsheet an appropriate name, such as "SwEng Students 2015".  Hover over the header fields in the sheet for additional help.

  **NOTE:** It is sufficient to fill only one of the ``GASPAR``, ``Name``, ``E-mail``, or ``SCIPER`` fields.  The tool will later fill in the missing data from the EPFL LDAP directory.

  **NOTE:** It is important to leave the headers intact, as the tool looks up columns by their header name.

  4. Configure the tool by editing the ``config.yaml`` file.  You should change at least the following fields:

    * ``spreadsheet.title`` should contain the name of the Google Sheets document created at step 3 (e.g., ``SwEng Students 2015``).
    * ``organization.name`` should contain the identifier of the GitHub organization created at step 2 (e.g., ``sweng-epfl-2015``).
    * ``organization.staff-team-id`` and ``organization.class-team-id`` should contain the IDs of the staff and class teams created at step 2.
    * ``google_auth.client_id`` and ``google_auth.client_secret`` should point to the Google credentials the tool should use to access the spreadsheet.  You can create these credentials in the [Google Developer Console](https://console.developers.google.com).  First, create a new project, then go to "APIs & auth" / "Credentials", then add an "OAuth 2.0 client ID" credential.

  5. Verify your setup by running the tool in "repair" mode, which fills in all the missing columns in the Students sheet:
      
      $ venv/bin/activate
      $ ./manage.py repair
      $ deactivate

  You should activate the virtual Python environment before using the tool and deactivate it when no longer needed.

## Usage

Run ``./manage.py -h`` to see a list of possible commands.  Below is a (possibly outdated) snapshot:

    $ ./manage.py -h
    usage: manage.py [-h] [-c CONFIG] [-a AUTH] [-d] [-n]
                     
                     {students-list,students-perm,students-create,students-delete,teams-list,teams-perm,teams-create,teams-delete,repair,class-open,class-close}
                     ...
    
    Student repository management.
    
    positional arguments:
      {students-list,students-perm,students-create,students-delete,teams-list,teams-perm,teams-create,teams-delete,repair,class-open,class-close}
                            The operation to perform on the class
        students-list       List registered students.
        students-perm       Update student permissions.
        students-create     Create exam repos for students.
        students-delete     [DANGEROUS] Delete the exam repos of students.
        teams-list          List registered teams.
        teams-perm          Update teams permissions.
        teams-create        Create homework repos for teams.
        teams-delete        [DANGEROUS] Delete the homework repos of teams.
        repair              Repair the students spreadsheet.
        class-open          Open all team repositories to everyone.
        class-close         Hide all team repositories from everyone.
    
    optional arguments:
      -h, --help            show this help message and exit
      -c CONFIG, --config CONFIG
                            The configuration file to use. Relative paths are
                            appended to the script directory.
      -a AUTH, --auth AUTH  The authentication cache file to use. Relative paths
                            are appended to the script directory.
      -d, --debug           More verbose logging of actions
      -n, --non-interactive
                            Refrain from requesting user input. Useful when using
                            the command in batch mode.


[template]: https://docs.google.com/spreadsheets/d/1lSOhkBQrs7RRY0a-IoyfQRqvfp2kWnB-XvMBX-omfUY/edit#gid=0


## Setting Up

Perform the following steps in the base directory of the tool:

  1. Create a Python virtual environment:
  
        $ virtualenv venv
        $ source venv/bin/activate
  
  2. Install all tool dependencies:
  
        $ pip install -r requirements.txt
      
  3. Customize the ``config.yaml`` with your own course information and Google API client credentials.
  
  4. Create a Google spreadsheet using the title configured in ``config.yaml``, having the following structure:
    * A ``Students`` sheet with the following columns:
      * ``GASPAR`` - The EPFL student username
      * ``Name`` - Full name of the student
      * ``E-mail`` - EPFL e-mail address of the student
      * ``SCIPER`` - The EPFL student number
      * ``Team`` - The ID of the student team
      * ``Github ID`` - Student Github ID
      * ``EdX ID`` - (Optional) Student EdX ID
    * A ``Teams`` sheet with the following columns:
      * ``Team`` - The team ID
      * ``Github Slug`` - A Github-friendly identifier to be used in repo names
  
  It is sufficient to fill only one of the ``GASPAR``, ``Name``, ``E-mail``, or ``SCIPER`` fields. The next step will recostruct all information from the EPFL LDAP directory.
      
  5. Run ``./manage.py repair`` in order to fill in all missing information in the ``Students`` sheet.
  
  6. Run ``./manage.py -h`` to see a list of possible commands to invoke next.

## Usage

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

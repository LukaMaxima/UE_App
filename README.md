# Ultimate Europe - Companion App: README v0.4

## Scope

1. This is an attempt to automate some of the more time-consuming and (if you’re anything like me) prone-to-human-error aspects of playing Ultimate Europe using Python.

2. Benefits include:
   - Automated PV calculations across First, Reserve, and Youth teams.
   - Easy team selections without player codes using auto-filtering dropdowns to select your teams.
   - Automated MDS submissions for all teams, including automated code inputs.
   - Save data locally to submit your MDS later, allowing rapid resubmissions.
   - Alerts if a player has a low or N/A PV for the chosen position.
   - Automated scouting (currently limited to country).

## Installation

### Download & Unzip

3. Download the `zip` file by clicking the green `Code` button and selecting `download zip`. Once downloaded, right-click the .zip file and extract it to where you want it to be (I just run mine from my desktop.)

---

### Installation Requirements

To run the app, you will need to ensure a number of software packages are installed on your machine, as follows:

#### Python

6. Python 64-bit for Windows. This was developed and tested on Python version 3.12.2, available here:  
   [Download Python 3.12.2 (64-bit)](https://www.python.org/ftp/python/3.12.2/python-3.12.2-amd64.exe)

#### Java

7. Java 64-bit for Windows. This was developed and tested on Java version 1.8.0_401, available here:  
   [Download Java](https://www.java.com/en/download/)

---

### Python Packages

8. The app requires a handful of Python packages to run. These are listed in `requirements.txt`. To install them:
   - Right-click the `Install Python Packages.ps1` file and select **Run with PowerShell**.

9. This process may take some time. If at any time it says “requirement already satisfied,” this is totally fine. Sometimes Python packages have already installed other dependencies.

---

### Firefox and Chrome

10. The scripts will use both Firefox and Chrome. Both must be installed for the code to work correctly. If you already have them installed, you can skip this section.

   - [Download Firefox](https://www.mozilla.org/en-GB/firefox/windows/)  
   - [Download Chrome](https://www.google.com/intl/en_uk/chrome/)  

   Once both are installed, you’re ready to use the app.

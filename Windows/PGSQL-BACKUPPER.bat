@REM  Author: Orbit Turner
@echo off
chcp 65001


echo "=======================================================";
echo "  ____   ____       ____    _    ____ _  ___   _ ____  ";
echo " |  _ \ / ___|     | __ )  / \  / ___| |/ / | | |  _ \ ";
echo " | |_) | |  _ _____|  _ \ / _ \| |   | ' /| | | | |_) |";
echo " |  __/| |_| |_____| |_) / ___ \ |___| . \| |_| |  __/ ";
echo " |_|    \____|     |____/_/   \_\____|_|\_\\___/|_|    ";
echo "                 PGSQL DB BACKUPPER                    ";
echo "=======================================================";
echo "    Follow : @OrbitTurner • https://orbitturner.com    ";
echo "=======================================================";


@REM  This is a batch script to backup the database using PostgreSQL backup utility "pg_dump".
@REM  You can add this script to Windows Task Scheduler and define your custom backup routine.
	

REM "Set following backup parameters to take backup"
SET PGPASSWORD=FBIOPENTHEDOOR
SET db_name=baseName
SET file_format=c
SET host_name=localhost
SET user_name=uname
SET pg_dump_path="C:\<YOUR-PG-INSTALL-DIR>\PostgreSQL\14\bin\pg_dump.exe"  
SET target_backup_path=C:\MyPGBackupDir\
SET other_pg_dump_flags=--blobs --verbose -c 

REM Fetch Current System Date and set month,day and year variables
SET day=%date:~0,2%
SET month=%date:~3,2%
SET year=%date:~6,4%
SET hour=%time:~0,2%
SET min=%time:~3,2%


REM Creating string for backup file name
for /f "delims=" %%i in ('dir "%target_backup_path%" /b/a-d ^| find /v /c "::"') do set count=%%i
set /a count=%count%+1 
set datestr=backup_%year%_%month%_%day%_%hour%_%min%
set BackupSubFolder=VS-snapshot_%year%-%month%-%day%
REM CREATING BACKUP SUBFOLDER FOLDER FOR THE DAY
mkdir %target_backup_path%%BackupSubFolder%

REM Backup File name
set BACKUP_FILE=pg_%db_name%_%datestr%.dump

REM :> Executing command to backup database
%pg_dump_path% --host=%host_name% -U %user_name% --format=%file_format%  %other_pg_dump_flags% -f %target_backup_path%%BackupSubFolder%\%BACKUP_FILE%  %db_name% 
if ERRORLEVEL  NEQ 0 do (
  echo SOMETHING BAD HAPPENED > Log.txt
  pause
)
pause
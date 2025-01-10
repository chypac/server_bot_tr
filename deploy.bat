@echo off
echo Deploying changes to GitHub...

:: Проверяем инициализацию Git
if not exist .git (
    echo Initializing Git repository...
    git init
    git remote add origin git@github.com:chypac/server_bot_tr.git
)

:: Добавляем все изменения
git add .

:: Запрашиваем сообщение коммита
:input_message
set /p commit_msg="Enter commit message (cannot be empty): "
if "%commit_msg%"=="" (
    echo Commit message cannot be empty!
    goto input_message
)

:: Делаем коммит и пуш
git commit -m "%commit_msg%"
git push -u origin master

echo.
echo Changes deployed successfully!
echo Run update.sh on your server to apply these changes.
pause

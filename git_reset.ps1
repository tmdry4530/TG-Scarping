# Git 저장소 초기화 스크립트
Write-Host "현재 디렉토리의 Git 설정을 초기화합니다..." -ForegroundColor Yellow

# .git 디렉토리 삭제
if (Test-Path -Path ".git") {
    Write-Host ".git 디렉토리를 삭제합니다..." -ForegroundColor Cyan
    Remove-Item -Path ".git" -Recurse -Force
    Write-Host ".git 디렉토리가 삭제되었습니다." -ForegroundColor Green
} else {
    Write-Host ".git 디렉토리가 없습니다." -ForegroundColor Magenta
}

# 깃 관련 설정 파일 삭제
$gitFiles = @(
    ".gitignore",
    ".gitattributes",
    ".gitmodules",
    ".github"
)

foreach ($file in $gitFiles) {
    if (Test-Path -Path $file) {
        Write-Host "$file 을(를) 삭제합니다..." -ForegroundColor Cyan
        if (Test-Path -Path $file -PathType Container) {
            Remove-Item -Path $file -Recurse -Force
        } else {
            Remove-Item -Path $file -Force
        }
        Write-Host "$file 이(가) 삭제되었습니다." -ForegroundColor Green
    }
}

Write-Host "깃 초기화가 완료되었습니다!" -ForegroundColor Yellow
Write-Host "새 Git 저장소를 초기화하려면 'git init' 명령어를 실행하세요." -ForegroundColor Cyan 
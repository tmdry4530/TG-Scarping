#!/bin/bash

# Git 저장소 초기화 스크립트
echo "현재 디렉토리의 Git 설정을 초기화합니다..."

# .git 디렉토리 삭제
if [ -d ".git" ]; then
    echo ".git 디렉토리를 삭제합니다..."
    rm -rf .git
    echo ".git 디렉토리가 삭제되었습니다."
else
    echo ".git 디렉토리가 없습니다."
fi

# 깃 관련 설정 파일 삭제
git_files=(".gitignore" ".gitattributes" ".gitmodules")

for file in "${git_files[@]}"; do
    if [ -e "$file" ]; then
        echo "$file 을(를) 삭제합니다..."
        rm -f "$file"
        echo "$file 이(가) 삭제되었습니다."
    fi
done

# .github 디렉토리 삭제
if [ -d ".github" ]; then
    echo ".github 디렉토리를 삭제합니다..."
    rm -rf .github
    echo ".github 디렉토리가 삭제되었습니다."
fi

echo "깃 초기화가 완료되었습니다!"
echo "새 Git 저장소를 초기화하려면 'git init' 명령어를 실행하세요." 
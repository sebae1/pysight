# PySight
- **Keysight MSO-X 3104A** 오실로스코프 데이터 취득 프로그램
- VISA API를 사용하는 USB 인터페이스 오실로스코프라면 위 모델이 아니더라도 사용 가능할 수도..
- [🚀 **실행 파일 다운로드**](https://1drv.ms/u/s!AmwiopiWLJy7ouMqOMZ0siiHQV6Bew?e=xhzPLa)

## 실행 환경
- 프로그램 실행
    - 윈도우10 64 비트 이상
    - (Optional) Keysight Connection Expert
    - (Optional) NI-VISA
- 코딩
    - Python 3.11
    - `requirements.txt` 참조

## 패키징 하기
- 소스 코드 수정 후 실행 파일로 만들고자 하면 아래와 같이 하세요. 
    1. Python 3.11 버전의 가상환경 생성
        - pyvenv, anaconda, miniconda 등 이용
    2. 가상환경 활성화
    3. 라이브러리 설치
        - `pip install -r requirements.txt`
    4. 패키징
        - `pyinstaller PySight.spec`
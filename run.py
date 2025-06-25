from app import create_app

# 앱 초기화
app = create_app()

# 애플리케이션 실행
if __name__ == '__main__':
    app.run(debug=True)  # 디버그 모드에서 실행, 운영 환경에서는 False로 설정

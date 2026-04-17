🛠 1. Yêu cầu hệ thống

Python:  3.12 

nvm : Đã cài đặt trên máy.

Poetry: Đã cài đặt trên máy.

PostgreSQL: Đang chạy local hoặc server.

📥 2. Cài đặt nhanh (Setup)

Bước 1: Clone dự án và truy cập thư mục

Bash
git clone <link_repo_cua_team>
cd backend-ai
Bước 2: Cấu hình môi trường ảo

Bash
# Ép Poetry tạo folder .venv ngay tại project cho dễ quản lý
poetry config virtualenvs.in-project true

# Cài đặt tất cả thư viện (FastAPI, SQLAlchemy, TensorFlow, NLTK...)
poetry add fastapi uvicorn[standard] sqlalchemy psycopg2-binary python-dotenv pydantic-settings nltk tensorflow
Bước 3: Cấu hình file .env
Tạo file .env ở thư mục gốc với nội dung:

Đoạn mã
DATABASE_URL=postgresql://<user>:<password>@localhost:5432/<db_name>
PROJECT_NAME="EpicCV_AI_Backend"


🏃 3. Chạy ứng dụng
Sử dụng lệnh sau để bật server:

Bash
poetry run uvicorn app.main:app --reload
🔗 4. Kiểm tra kết nối
Mở trình duyệt và truy cập các đường dẫn sau:

Trang chủ: http://127.0.0.1:8000/

Swagger UI (Dùng để test API): http://127.0.0.1:8000/docs

Test AI: http://127.0.0.1:8000/test-ai (Kiểm tra xem TensorFlow/NLTK đã load chưa).

📁 5. Cấu trúc thư mục chính
app/main.py: File chạy chính của server.

app/core/config.py: Đọc cấu hình từ file .env.

app/db/database.py: Quản lý kết nối PostgreSQL.

app/services/: Chứa các logic xử lý AI và nghiệp vụ.


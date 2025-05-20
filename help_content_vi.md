# help_content_vi.md
# Hướng Dẫn Sử Dụng MP4 Looper

## Tổng Quan
MP4 Looper giúp bạn tạo các video lặp kéo dài với nhạc nền từ các file MP4 gốc. Ứng dụng được thiết kế để tạo video lặp với các bài hát nền được lấy từ danh sách phát trên Google Sheet.

## Tính Năng Chính
- Lặp video MP4 theo thời lượng chỉ định (1h, 3h, 11h, hoặc tùy chỉnh)
- Tự động thêm nhạc nền từ thư viện nhạc
- Xuất danh sách bài hát có mốc thời gian
- Xử lý hàng loạt nhiều file
- Tự động tải lên Google Drive

## Bắt Đầu Sử Dụng

### 1. Thêm File
- **Kéo và Thả**: Kéo file MP4 hoặc thư mục trực tiếp vào ứng dụng
- **Duyệt**: Nhấp "Browse Files" để chọn file MP4

### 2. Thiết Lập Thời Lượng
- Nhập thời lượng tùy chỉnh bằng giây
- Hoặc sử dụng các nút cài đặt nhanh: +1h (3600s), +3h (10800s), +11h (39600s)

### 3. Cài Đặt Thư Mục
- **Output Folder**: Nơi lưu video đã xử lý
- **Music Folder**: Thư mục chứa file nhạc WAV cho phần nền

### 4. Cấu Hình Nhạc
- **Google Sheet URL**: Bảng tính chứa cơ sở dữ liệu bài hát của bạn
- **Default Songs**: Sử dụng 5 bài hát mới nhất từ danh sách hoặc đặt số lượng tùy chỉnh

### 5. Tùy Chọn Xử Lý
- **Fade Audio**: Thêm hiệu ứng làm mờ âm thanh 5 giây ở cuối
- **Export Timestamp**: Tạo file mốc thời gian cho bài hát
- **Auto-Upload**: Tự động tải lên Google Drive sau khi xử lý

### 6. Bắt Đầu Xử Lý
Nhấp "Start Processing" để bắt đầu. Ứng dụng sẽ:
1. Tạo danh sách bài hát cho mỗi video
2. Tạo video lặp kéo dài với nhạc
3. Xuất file mốc thời gian cho mỗi video
4. Tải lên Google Drive (nếu được chọn)

## Yêu Cầu Video
- File phải ở định dạng MP4
- Không có yêu cầu mã hóa đặc biệt - luồng video gốc được tái sử dụng

## Yêu Cầu Nhạc
- File WAV trong thư mục nhạc
- Tên file phải khớp với định dạng trong Google Sheet
- Ví dụ: "123_Tên Bài Hát.wav"

## Sử Dụng Tính Năng Tải Lên Google Drive
1. Đảm bảo bạn có thông tin xác thực Google API hợp lệ (credentials.json)
2. Chọn "Auto-upload after render" hoặc sử dụng nút "Upload to Drive"
3. File sẽ được sắp xếp theo tiền tố số trong Google Drive

## Xử Lý Sự Cố

### Thiếu File Nhạc
Nếu bạn gặp lỗi "Missing WAV Files":
- Kiểm tra xem thư mục nhạc có chứa tất cả file WAV cần thiết không
- Đảm bảo tên file khớp với định dạng trong bảng tính (ví dụ: "123_Tên Bài Hát.wav")
- Thử sử dụng cài đặt trước bảng tính khác

### Lỗi Render
Nếu việc render thất bại:
- Kiểm tra nhật ký gỡ lỗi (debug log) để biết lỗi cụ thể
- Đảm bảo FFmpeg được cài đặt đúng cách
- Xác minh rằng video đầu vào là file MP4 hợp lệ

### Vấn Đề Tải Lên
Nếu việc tải lên thất bại:
- Kiểm tra kết nối internet
- Xác minh thông tin xác thực Google API
- Sử dụng "Clean Canceled Uploads" để xóa các tải lên bị treo

## Mẹo
- Để có kết quả tốt nhất, hãy sử dụng video nguồn chất lượng cao
- Ứng dụng giữ nguyên chất lượng video gốc
- Sử dụng các nút "Clean" để quản lý không gian đĩa sau khi xử lý
- Kiểm tra nhật ký gỡ lỗi để biết thông tin chi tiết về các hoạt động
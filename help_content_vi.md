# MP4 Looper - Hướng Dẫn Sử Dụng

Chào mừng bạn đến với MP4 Looper! Ứng dụng này giúp bạn tạo video dài bằng cách kết hợp file video với nhạc nền. Hoàn hảo để tạo nội dung kéo dài cho streaming hoặc video môi trường.

## 🚀 Bắt Đầu

### Những Gì Bạn Cần Chuẩn Bị
1. **File Video**: Các file MP4 bạn muốn lặp lại
2. **File Nhạc**: Các file âm thanh WAV làm nhạc nền
3. **Tài Khoản Google**: Để truy cập danh sách nhạc và upload (tùy chọn)
4. **Dung Lượng Lưu Trữ**: Đủ không gian đĩa cho video đầu ra

### Thiết Lập Lần Đầu
1. **Khởi Động Ứng Dụng**: Click đúp vào biểu tượng MP4 Looper
2. **Đăng Nhập**: Nhập email và mật khẩu khi được yêu cầu
3. **Thiết Lập Thư Mục**: Cấu hình thư mục đầu ra và thư mục nhạc

## 📁 Thiết Lập Thư Mục

### Thư Mục Đầu Ra (Output Folder)
- **Là gì**: Nơi lưu các video đã hoàn thành
- **Cách thiết lập**: Click "Browse" bên cạnh "Output Folder"
- **Lời khuyên**: Chọn thư mục có nhiều dung lượng trống (video có thể rất lớn!)

### Thư Mục Nhạc (Music Folder)
- **Là gì**: Thư mục chứa các file nhạc WAV
- **Định dạng file**: Chỉ hỗ trợ file WAV (.wav)
- **Tổ chức**: Giữ tất cả file nhạc trong một thư mục để dễ truy cập

## 🎵 Thiết Lập Danh Sách Nhạc

### Tích Hợp Google Sheets
Ứng dụng có thể đọc danh sách nhạc từ Google Sheets:

1. **Tạo Google Sheet** với các cột sau:
   - Cột A: Số thứ tự bài hát (1, 2, 3, v.v.)
   - Cột B: Tên bài hát (phải khớp với tên file WAV)
   - Cột C: Tên kết hợp (tự động tạo: "1_TenBaiHat")
   - Cột E: Ngày tuần (định dạng MM/DD/YYYY)

2. **Ví dụ bố cục Sheet**:
   ```
   A    | B           | C           | D | E
   1    | Amazing     | 1_Amazing   |   | 01/15/2024
   2    | Wonderful   | 2_Wonderful |   | 01/15/2024
   3    | Beautiful   | 3_Beautiful |   | 01/22/2024
   ```

3. **Lấy URL Sheet**: Copy URL chia sẻ của Google Sheet
4. **Dán vào App**: Dán URL vào ô "Google Sheet URL"

### Cách Đặt Tên File Nhạc
File WAV của bạn phải khớp với tên trong Google Sheet:
- Sheet ghi "Amazing" → File phải là "Amazing.wav"
- Sheet ghi "Wonderful" → File phải là "Wonderful.wav"

## 🎬 Tạo Video

### Bước 1: Thêm File Video
**Phương pháp Kéo Thả** (Dễ nhất):
1. Mở thư mục chứa file MP4
2. Kéo file trực tiếp vào cửa sổ ứng dụng
3. File xuất hiện ở phần "Raw Preview"

**Phương pháp Browse**:
1. Click nút "Browse Files"
2. Chọn file MP4 của bạn
3. Click "Open"

### Bước 2: Thiết Lập Thời Lượng Video
1. **Ô Duration**: Nhập thời gian bằng giây
   - 3600 = 1 giờ
   - 7200 = 2 giờ
   - 10800 = 3 giờ
2. **Nút Nhanh**: Dùng nút +1h, +3h, +11h cho thời lượng phổ biến
3. **Xem trước**: Xem chuyển đổi thời gian (ví dụ: "3600s (1h)")

### Bước 3: Cấu Hình Thiết Lập

**Thiết Lập Bài Hát**:
- **"Use default (5) newest songs"**: App tự động chọn 5 bài hát mới nhất
- **Số lượng tùy chỉnh**: Bỏ tick và nhập số lượng bạn muốn

**Tùy Chọn Âm Thanh**:
- **"Fade audio out at end"**: Giảm dần âm lượng trong 5 giây cuối
- **"Export timestamp"**: Tạo file text hiển thị thời điểm phát mỗi bài

**Tùy Chọn Upload** (Chỉ Admin):
- **"Auto-upload after render"**: Tự động upload video đã hoàn thành

### Bước 4: Bắt Đầu Xử Lý
1. **Kiểm tra Thiết Lập**: Kiểm tra lại tất cả thiết lập
2. **Click "Start Processing"**: Bắt đầu quá trình!
3. **Theo dõi Tiến độ**: Xem thanh tiến độ và thông báo trạng thái
4. **Chờ đợi**: Thời gian xử lý phụ thuộc vào độ dài video và tốc độ máy tính

## 🔧 Tính Năng Nâng Cao

### Chế Độ Phân Phối Bài Hát
Tạo nhiều video với các lựa chọn bài hát khác nhau:

1. **Click "Song Distribution"**: Mở thiết lập phân phối
2. **Đặt Số Lượng Video**: Chọn số lượng phiên bản khác nhau cần tạo
3. **Phương Pháp Phân Phối**:
   - **Sequential**: Bài hát được chia theo thứ tự (1-10, 11-20, v.v.)
   - **Random**: Bài hát được trộn ngẫu nhiên cho mỗi video
4. **Xem trước**: Xem chính xác bài hát nào mỗi video sẽ sử dụng
5. **Bắt Đầu Xử Lý**: Tạo nhiều video độc đáo

### Hiệu Ứng Chuyển Cảnh Video 🎬

MP4 Looper giờ đây hỗ trợ các hiệu ứng chuyển cảnh chuyên nghiệp ở đầu và cuối video:

**Các Hiệu Ứng Có Sẵn:**
- **None** - Không có hiệu ứng (mặc định)
- **Fade** - Hiệu ứng mờ dần vào/ra
- **Slide Left/Right** - Video trượt từ trái hoặc phải
- **Zoom** - Phóng to khi bắt đầu, thu nhỏ khi kết thúc
- **Wipe Down/Up** - Video hiện dần từ trên xuống hoặc dưới lên
- **Blinds** - Hiệu ứng rèm ngang
- **Pixelate** - Làm mờ pixel rồi hiện rõ dần
- **Dissolve** - Hiệu ứng tan biến ngẫu nhiên
- **Expand Line** - Mở rộng từ đường trung tâm

**Lưu Ý Quan Trọng:**
- Cần có GPU NVIDIA với hỗ trợ NVENC
- Mỗi hiệu ứng thêm ~1.5 giây vào đầu và cuối video
- Nếu không có GPU, video vẫn xử lý bình thường nhưng không có hiệu ứng
- Hiệu ứng hoạt động với mọi thời lượng video (1h, 3h, 11h)

**Cách sử dụng:**
1. Chọn hiệu ứng mong muốn từ menu thả xuống
2. Hiệu ứng sẽ áp dụng cho tất cả video trong hàng đợi
3. Theo dõi tiến trình - bạn sẽ thấy "Applying [tên hiệu ứng] transition..." khi xử lý

### Cửa Sổ Tiện Ích
Click nút 🔧 để truy cập các công cụ bổ sung:

**Công Cụ Debug**:
- **View Log**: Xem hoạt động chi tiết của app (để khắc phục sự cố)
- **Clean Uploads**: Xóa các lần upload bị lỗi

**Công Cụ Hỗ Trợ**:
- **Send Debug Info**: Chia sẻ log với đội hỗ trợ (nếu cần)
- **Help**: Mở hướng dẫn này

**Công Cụ Admin** (Chỉ người dùng Admin):
- **Monitor**: Xem thống kê sử dụng chi tiết

## 📤 Quản Lý File

### File Đầu Ra
Sau khi xử lý, bạn sẽ tìm thấy các file này trong thư mục đầu ra:

**File Video**:
- `TenVideo_1h.mp4` - Video hoàn thành của bạn
- `TenVideo_3h.mp4` - Nếu bạn tạo phiên bản 3 giờ

**File Thông Tin**:
- `TenVideo_song_list.txt` - Danh sách bài hát đã sử dụng
- `TenVideo_song_list_timestamp.txt` - Thời điểm phát mỗi bài hát
- `temp_music.wav` - Track âm thanh kết hợp (tự động xóa)

### Quản Lý File
**Mở Thư Mục Đầu Ra**: Click "Open" bên cạnh Output Folder để xem file
**Dọn Dẹp Thư Mục**: Click "Clean" để xóa file cũ (cẩn thận!)

## ❗ Khắc Phục Sự Cố

### Vấn Đề Thường Gặp và Giải Pháp

**"No files queued for processing"**
- **Vấn đề**: Bạn chưa thêm file video nào
- **Giải pháp**: Kéo thả file MP4 vào ứng dụng

**"Missing WAV files"**
- **Vấn đề**: App không tìm thấy file nhạc khớp với danh sách
- **Giải pháp**: 
  1. Kiểm tra đường dẫn Music Folder
  2. Xác minh tên file WAV khớp chính xác với Google Sheet
  3. Đảm bảo file thực sự có định dạng .wav

**"Failed to generate song list"**
- **Vấn đề**: Không thể truy cập Google Sheet
- **Giải pháp**:
  1. Kiểm tra kết nối internet
  2. Xác minh URL Google Sheet đúng
  3. Đảm bảo sheet được chia sẻ công khai

**"Output folder does not exist"**
- **Vấn đề**: Đường dẫn thư mục đầu ra không hợp lệ
- **Giải pháp**: Click "Browse" và chọn thư mục hợp lệ

**"Authentication failed"**
- **Vấn đề**: Thông tin đăng nhập không đúng
- **Giải pháp**: 
  1. Kiểm tra lại email và mật khẩu
  2. Liên hệ quản trị viên để được cấp quyền truy cập
  3. Chờ vài phút nếu bạn đã thử quá nhiều lần

**Xử lý mất quá nhiều thời gian**
- **Nguyên nhân có thể**: 
  1. Thời lượng video rất dài
  2. Nhiều file video lớn
  3. Máy tính thiếu tài nguyên
- **Giải pháp**:
  1. Xử lý ít file hơn cùng lúc
  2. Sử dụng thời lượng ngắn hơn để thử nghiệm
  3. Đóng các chương trình khác để giải phóng bộ nhớ

**"GPU not detected"**
- **Vấn đề**: Không có tăng tốc phần cứng
- **Giải pháp**: Xử lý sẽ chậm hơn nhưng vẫn hoạt động

### Nhận Trợ Giúp
1. **Kiểm tra Log**: Dùng "View Log" trong tiện ích để xem chi tiết lỗi
2. **Gửi Debug Info**: Dùng "Send Debug Info" để chia sẻ log với hỗ trợ
3. **Liên hệ Hỗ trợ**: Liên hệ với thông báo lỗi cụ thể

## 💡 Mẹo Để Có Kết Quả Tốt Nhất

### Mẹo Hiệu Suất
1. **Xử lý theo lô**: Đừng xếp hàng quá nhiều file lớn cùng lúc
2. **Giải phóng dung lượng**: Đảm bảo nhiều dung lượng trống trong thư mục đầu ra
3. **Đóng app khác**: Cho MP4 Looper nhiều tài nguyên hệ thống hơn
4. **Sử dụng SSD**: Lưu trữ nhanh hơn = xử lý nhanh hơn

### Mẹo Chất Lượng
1. **Sử dụng video nguồn chất lượng cao**: Chất lượng đầu ra tương ứng chất lượng đầu vào
2. **Tổ chức nhạc tốt**: Giữ file WAV được tổ chức và đặt tên đúng
3. **Thử với thời lượng ngắn**: Thử video 3 phút trước khi tạo video dài giờ
4. **Sao lưu thường xuyên**: Lưu video hoàn thành vào lưu trữ ngoài

### Mẹo Quy Trình
1. **Chuẩn bị file trước**: Tổ chức video và nhạc trước khi bắt đầu
2. **Sử dụng cách đặt tên nhất quán**: Giữ tên file đơn giản và nhất quán
3. **Cập nhật danh sách thường xuyên**: Giữ Google Sheet luôn cập nhật
4. **Lưu thiết lập**: App nhớ các tùy chọn của bạn

## 🔒 Quyền Riêng Tư và Bảo Mật

- **Xử lý Cục bộ**: Video được xử lý trên máy tính của bạn
- **Đăng nhập Bảo mật**: Xác thực được mã hóa và an toàn
- **Upload Tùy chọn**: Bạn kiểm soát việc video có được upload đâu không
- **Quyền riêng tư Log**: Log debug chứa đường dẫn file nhưng không có nội dung cá nhân

## 📋 Phím Tắt

- **Kéo & Thả**: Thêm file bằng cách kéo từ file explorer
- **Enter**: Xác nhận thiết lập trong hộp thoại
- **Escape**: Hủy thao tác hoặc đóng hộp thoại

---

**Cần thêm trợ giúp?** Sử dụng tính năng "Send Debug Info" để liên hệ hỗ trợ với thông tin chi tiết về bất kỳ vấn đề nào bạn đang gặp phải.
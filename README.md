# HỆ THỐNG QUẢN LÝ NHÂN KHẨU CẤP XÃ
**Đơn vị sử dụng:** Công an Phường Nông Trang
**Phiên bản:** 1.0.0 (Chạy Offline 100%)

---

## 📌 GIỚI THIỆU PHẦN MỀM
Phần mềm Desktop **Hệ thống Quản lý Nhân khẩu Cấp xã** được phát triển bằng ngôn ngữ Python 3.11+ và thư viện PyQt5, SQLite3. Phần mềm phục vụ công tác quản lý địa bàn, nhân khẩu, hộ gia đình của cán bộ Công an xã và cán bộ phụ trách quản lý hành chính công.

### 🌟 Tính năng nổi bật:
* **Giao diện chuẩn GOV Việt Nam:** Tone màu chủ đạo Đỏ đô (`#A6192E`) và Xanh Navy (`#17365D`), trang trọng, hiện đại, thân thiện.
* **Dashboard Thống kê trực quan:** Tích hợp 4 biểu đồ Matplotlib (Dân số theo khu vực, Cơ cấu giới tính Donut, Cơ cấu độ tuổi, Số lượng hộ gia đình).
* **Quản lý Nhân khẩu (CRUD):** Thêm mới, xem chi tiết, chỉnh sửa, xóa mềm/khôi phục bản ghi. Form thiết kế 4 Tabs hiện đại.
* **Tìm kiếm thông minh:** Tìm kiếm không dấu tiếng Việt (NFD) realtime với thời gian phản hồi cực nhanh.
* **Quản lý Hộ gia đình:** Liên kết các thành viên trong hộ, chuyển hộ, chọn chủ hộ.
* **Quản lý Khu vực / Thôn / Tổ dân phố:** Phân chia địa bàn và chuyển nhân khẩu giữa các khu.
* **Import Excel chuyên nghiệp:** Xem trước 20 dòng, tự động nhận diện ánh xạ cột, xử lý giữ nguyên số 0 ở đầu CCCD/SĐT, kiểm tra trùng lặp và hỗ trợ Transaction an toàn.
* **Export Excel báo cáo:** Định dạng chuẩn báo cáo hành chính công, tự động auto-fit cột, đóng băng tiêu đề (Freeze pane), AutoFilter.
* **Bảo mật & Phân quyền (RBAC):** Mật khẩu băm PBKDF2-SHA256 kèm Salt, ẩn số CCCD/SĐT nếu không đủ quyền, tự động lưu Nhật ký hoạt động (Audit Log).
* **Sao lưu & Phục hồi DB:** Tự động tạo snapshot trước khi khôi phục, kiểm tra tính toàn vẹn SQLite.

---

from app.attendance.service import AttendanceService

def test_percentage():
    service = AttendanceService()
    assert service.calculate_percentage(17, 20) == 85.0
    assert service.calculate_percentage(0, 0) == 0.0

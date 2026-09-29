import pandas as pd
import random
from datetime import datetime, timedelta

records = []

attendance_no = 3451

start_date = datetime(2026, 8, 1)
end_date = datetime(2026, 8, 12)

dates = []
current = start_date
while current <= end_date:
    dates.append(current)
    current += timedelta(days=1)

for emp in range(1, 151):

    employee_id = f"EMP{emp:03d}"

    for d in dates:

        # Random Check-In (08:50 to 09:20)
        checkin_minutes = random.randint(0, 30)
        checkin_seconds = random.randint(0, 59)
        check_in = datetime.combine(
            d.date(),
            datetime.strptime("08:50:00", "%H:%M:%S").time()
        ) + timedelta(minutes=checkin_minutes, seconds=checkin_seconds)

        # Random Check-Out (17:50 to 18:30)
        checkout_minutes = random.randint(0, 40)
        checkout_seconds = random.randint(0, 59)
        check_out = datetime.combine(
            d.date(),
            datetime.strptime("17:50:00", "%H:%M:%S").time()
        ) + timedelta(minutes=checkout_minutes, seconds=checkout_seconds)

        records.append([
            f"ATT{attendance_no:06d}",
            employee_id,
            d.strftime("%Y-%m-%d"),
            check_in.strftime("%H:%M"),
            check_out.strftime("%H:%M"),
            "Present"
        ])

        attendance_no += 1

df = pd.DataFrame(records, columns=[
    "Attendance_ID",
    "Employee_ID",
    "Attendance_Date",
    "Check_In_Time",
    "Check_Out_Time",
    "Status"
])

df.to_csv("attendance_august.csv", index=False)

print("Generated", len(df), "records")
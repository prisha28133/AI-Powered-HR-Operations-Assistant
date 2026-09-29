from recommendation import generate_recommendation

employee_request = """
Intent : Attendance Correction

Employee ID : EMP1045

Attendance Date : 2026-07-20

Correction Type : Missing Punch Out

Reason : Machine malfunctioned and punch-out was not recorded.
"""

policy = """
Attendance Correction Requests may be submitted for:

- Missing Check-in
- Missing Check-out
- Incorrect Check-in Time
- Incorrect Check-out Time

AI Validation Rules

The Employee ID exists in the Employee Master.

The Attendance Date is valid.

All mandatory information has been provided.

Decision Logic

If all validation rules are satisfied, the AI HR Operations Assistant shall generate an Approved recommendation.
"""

response = generate_recommendation(employee_request, policy)

print(response)
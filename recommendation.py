import ollama
import json

MODEL = "qwen2.5:3b"


def generate_recommendation(employee_request, policy, validation_result):


    # Convert employee request from JSON string to dictionary
    if isinstance(employee_request, str):
        try:
            employee_request = json.loads(employee_request)
        except json.JSONDecodeError:
            employee_request = {}

    validation_text = ""
    decision_rules = ""

    # =====================================================
    # LEAVE REQUEST
    # =====================================================

    if "leave_balance" in validation_result:

        validation_text = f"""
Employee Exists : {validation_result.get("employee_exists", False)}
Leave Type : {employee_request.get("leave_type", "Not Provided")}
Leave Balance : {validation_result.get("leave_balance", "Not Provided")}
Duplicate Request : {validation_result.get("duplicate", False)}
Leave Days : {validation_result.get("leave_days", "Not Provided")}
"""

        decision_rules = """
Leave Decision Rules:

1. Approve the request ONLY if ALL applicable conditions pass:
- Employee exists.
- Leave balance is sufficient for the requested Leave Days.
- The request is not a duplicate.
- The requested leave satisfies ALL applicable policy rules.
- Required information is available.

2. Paid Leave:
- Paid Leave can be taken for a maximum of 2 WORKING DAYS per request.
- Saturday and Sunday are NOT counted as leave days.
- Leave Days supplied in Validation Results is the VERIFIED working-day count.
- If Leave Type = Paid Leave AND Leave Days > 2:
  recommendation MUST be "Rejected".

3. Sick Leave and Casual Leave:
- Sick Leave and Casual Leave are treated as Paid Leave.
- Apply all Paid Leave rules after this classification.
- If the resulting Paid Leave request exceeds 2 working days,
  recommendation MUST be "Rejected".

4. Needs Human Review:
Recommend "Needs Human Review" ONLY when:
- A required eligibility condition cannot be verified.
- Required information needed for the decision is missing.
- The policy explicitly requires manual review.
- The request cannot be confidently validated using the supplied
  policy and database information.

5. Reject the request if:
- Employee does not exist.
- Leave balance is insufficient.
- The request is a duplicate.
- Leave Days exceeds the applicable policy limit.
- The request violates an applicable policy rule.
- The requested leave cannot be legally/policy-wise validated.

6. Leave Days:
- Leave Days are calculated by the application using working days only.
- Saturday and Sunday are excluded.
- Treat the supplied Leave Days as a VERIFIED value.
- Do NOT recalculate the number of days from calendar dates.

7. PRIORITY:
A verified rejection condition has higher priority than approval.

If ANY verified rejection condition is satisfied,
the recommendation MUST be "Rejected".

Never return "Approved" when a verified policy violation exists.
"""

    # =====================================================
    # WFH REQUEST
    # =====================================================

    elif "wfh_remaining" in validation_result:

        validation_text = f"""
Employee Exists : {validation_result.get("employee_exists", False)}
WFH Used : {validation_result.get("wfh_used", "Not Provided")}
WFH Remaining : {validation_result.get("wfh_remaining", "Not Provided")}
Duplicate Request : {validation_result.get("duplicate", False)}
"""

        decision_rules = """
WFH Decision Rules:

1. Approve ONLY if:
- Employee exists.
- WFH remaining days are sufficient.
- The request is not a duplicate.
- The requested WFH dates satisfy ALL applicable WFH policy rules.
- Required information is available.

2. Recommend "Needs Human Review" ONLY if:
- Required information is missing.
- A required policy condition cannot be verified.
- The request requires manual verification according to policy.
- The request cannot be confidently validated.

3. Reject if:
- Employee does not exist.
- WFH limit has been exceeded.
- The request is a duplicate.
- The request violates an applicable WFH policy rule.
- Requested dates are invalid.
- Requested dates are weekends/holidays where prohibited.

4. PRIORITY:
If any verified validation condition or policy rule requires rejection,
the recommendation MUST be "Rejected".

Never approve a request when a verified rejection condition exists.
"""

    # =====================================================
    # ATTENDANCE CORRECTION
    # =====================================================

    elif "attendance_exists" in validation_result:

        validation_text = f"""
Employee Exists : {validation_result.get("employee_exists", False)}
Attendance Exists : {validation_result.get("attendance_exists", False)}
Duplicate Request : {validation_result.get("duplicate", False)}
Within 3 Days : {validation_result.get("within_limit", False)}
Attendance Status : {validation_result.get("attendance_status", "Not Provided")}
Current Check-In : {validation_result.get("check_in", "Not Provided")}
Current Check-Out : {validation_result.get("check_out", "Not Provided")}
"""

        decision_rules = """
Attendance Decision Rules:

1. Approve ONLY if:
- Employee exists.
- Attendance record exists.
- Request is within the allowed 3-day limit.
- Request is NOT a duplicate.
- No applicable policy violation exists.

2. Needs Human Review:
Recommend "Needs Human Review" if the request involves:
- Attendance System Failure
- Network Connectivity Issue
- Biometric Device Failure
- Other exceptional operational/system issues
that require manual verification according to policy.

3. Reject if:
- Employee does not exist.
- Attendance record does not exist.
- Request is outside the 3-day limit.
- Request is a duplicate.
- The request violates an applicable attendance policy rule.

4. DUPLICATE HAS HIGHEST PRIORITY:
- If Duplicate Request = True,
  recommendation MUST be "Rejected".
- NEVER approve when Duplicate Request = True.
- Do not override or reinterpret this validation result.

5. FUTURE DATE:
- A future attendance date must be rejected.
"""

    # =====================================================
    # EMPLOYEE INFORMATION UPDATE
    # =====================================================

    elif "employee_information" in validation_result:

        validation_text = f"""
Employee Exists : {validation_result.get("employee_exists", False)}
"""

        decision_rules = """
Employee Information Update Decision Rules:

1. Approve ONLY if:
- Employee exists.
- The requested field is supported by the Employee Information Policy.
- The new value is valid.
- Required information is available.
- No policy restriction is violated.

2. Needs Human Review if:
- The requested update requires manual verification.
- Required information is missing.
- The request contains ambiguous information.
- The requested field cannot be confidently validated.

3. Reject if:
- Employee does not exist.
- The requested field is unsupported.
- The new value violates the applicable policy.
- The request is invalid.

Never approve an unsupported or invalid employee information update.
"""

    # =====================================================
    # UNKNOWN REQUEST TYPE
    # =====================================================

    else:

        validation_text = str(validation_result)

        decision_rules = """
General Decision Rules:

- Approve ONLY when the request can be completely validated.
- Reject when a verified policy violation exists.
- Recommend Needs Human Review when required information is missing
  or the request cannot be confidently validated.
- Never invent missing information.
"""


    # =====================================================
    # AI PROMPT
    # =====================================================

    prompt = f"""
You are an AI HR Operations Assistant.

Your task is to evaluate an employee request STRICTLY according
to the HR Policy provided below.

IMPORTANT:

1. Use ONLY the supplied HR Policy.
2. Do NOT use external HR knowledge.
3. Do NOT invent company rules.
4. Treat Validation Results as VERIFIED FACTS.
5. NEVER contradict a verified validation result.
6. Apply ALL applicable policy rules.
7. Do NOT ignore a policy restriction simply because other
   validation conditions passed.
8. Do NOT apply rules belonging to another request type.
9. Do NOT recalculate verified Leave Days.
10. Leave Days supplied by the application are already calculated
    using working days.
11. A verified policy violation MUST result in "Rejected".
12. "Needs Human Review" should ONLY be used when the policy
    or missing information genuinely prevents a final decision.
13. Do NOT automatically approve a request just because the
    employee exists and has sufficient balance.

CRITICAL DECISION PRIORITY:

FIRST check for verified rejection conditions.

If ANY applicable policy rule is violated:
    recommendation = "Rejected"

Otherwise check whether all required information and
eligibility conditions can be verified.

If they cannot:
    recommendation = "Needs Human Review"

Only if all applicable policy rules and validations pass:
    recommendation = "Approved"

For example:

If:
Leave Type = Paid Leave
AND
Leave Days = 4

and the policy says Paid Leave maximum = 2 working days,

then the recommendation MUST be:

"Rejected"

Even if:
- Employee exists
- Leave balance is sufficient
- Request is not duplicate

Do NOT return "Approved" in that situation.

Employee Request:

{employee_request}

Validation Results:

{validation_text}

{decision_rules}

Return ONLY one valid JSON object:

{{
    "recommendation": "Approved | Rejected | Needs Human Review",
    "reason": "Short explanation based only on the supplied policy and validation results."
}}

Relevant HR Policy:

{policy}
"""


    # =====================================================
    # CALL QWEN
    # =====================================================

    print(f"🤖 AI MODEL USED: {MODEL}")

    response = ollama.chat(
        model=MODEL,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    raw_response = response["message"]["content"]


    # =====================================================
    # PARSE AI RESPONSE
    # =====================================================

    try:

        recommendation = json.loads(raw_response)

    except json.JSONDecodeError:

        recommendation = {
            "recommendation": "Needs Human Review",
            "reason": "AI response was not valid JSON."
        }


    # =====================================================
    # SAFETY OVERRIDES / DETERMINISTIC FINAL DECISION
    # =====================================================
    #
    # IMPORTANT:
    # Qwen is used for policy interpretation, but it must NOT
    # override verified database/application validation facts.
    #
    # Therefore the final decision below is deterministic for
    # all conditions that the application has already verified.
    # =====================================================

    # -----------------------------------------------------
    # LEAVE REQUEST
    # -----------------------------------------------------

    if "leave_balance" in validation_result:

        employee_exists = validation_result.get(
            "employee_exists"
        )

        duplicate = validation_result.get(
            "duplicate"
        )

        leave_balance = validation_result.get(
            "leave_balance"
        )

        leave_type = employee_request.get(
            "leave_type",
            ""
        )

        leave_days = validation_result.get(
            "leave_days",
            0
        )

        try:
            leave_days = float(leave_days)

        except (ValueError, TypeError):
            leave_days = 0


        # -------------------------------------------------
        # EMPLOYEE DOES NOT EXIST
        # -------------------------------------------------

        if employee_exists is False:

            recommendation["recommendation"] = "Rejected"

            recommendation["reason"] = (
                "Employee does not exist in the Employee Master."
            )


        # -------------------------------------------------
        # DUPLICATE
        # -------------------------------------------------

        elif duplicate is True:

            recommendation["recommendation"] = "Rejected"

            recommendation["reason"] = (
                "The leave request is a duplicate of an existing "
                "leave request for the same employee and period."
            )


        # -------------------------------------------------
        # PAID LEAVE MAXIMUM
        # -------------------------------------------------

        elif (
            leave_type == "Paid Leave"
            and leave_days > 2
        ):

            recommendation["recommendation"] = "Rejected"

            recommendation["reason"] = (
                "Paid Leave cannot exceed 2 working days per request."
            )


        # -------------------------------------------------
        # SICK / CASUAL ARE TREATED AS PAID LEAVE
        # -------------------------------------------------

        elif (
            leave_type in ["Sick Leave", "Casual Leave"]
            and leave_days > 2
        ):

            recommendation["recommendation"] = "Rejected"

            recommendation["reason"] = (
                f"{leave_type} is treated as Paid Leave and "
                "cannot exceed 2 working days per request."
            )


        # -------------------------------------------------
        # INVALID / UNKNOWN LEAVE DAYS
        # -------------------------------------------------

        elif leave_days <= 0:

            recommendation["recommendation"] = "Needs Human Review"

            recommendation["reason"] = (
                "The application could not determine a valid number "
                "of working days for the leave request."
            )


        # -------------------------------------------------
        # BALANCE COULD NOT BE VERIFIED
        # -------------------------------------------------

        elif leave_balance is None:

            recommendation["recommendation"] = "Needs Human Review"

            recommendation["reason"] = (
                "Leave balance could not be verified from the "
                "Leave Balance record."
            )


        # -------------------------------------------------
        # INSUFFICIENT BALANCE
        # -------------------------------------------------

        else:

            try:
                balance = float(leave_balance)

            except (ValueError, TypeError):
                balance = None


            if balance is None:

                recommendation["recommendation"] = "Needs Human Review"

                recommendation["reason"] = (
                    "Leave balance could not be verified."
                )


            elif (
                leave_type in [
                    "Paid Leave",
                    "Sick Leave",
                    "Casual Leave"
                ]
                and balance < leave_days
            ):

                recommendation["recommendation"] = "Rejected"

                recommendation["reason"] = (
                    f"Insufficient Paid Leave balance. "
                    f"Available balance: {balance} days; "
                    f"requested: {leave_days} working day(s)."
                )


            else:

                # -------------------------------------------------
                # ALL VERIFIED LEAVE CONDITIONS PASSED
                # -------------------------------------------------
                #
                # DO NOT allow Qwen to turn a valid request into
                # a rejection such as "1 day exceeds 2 days".
                #

                recommendation["recommendation"] = "Approved"

                recommendation["reason"] = (
                    "Employee exists, leave balance is sufficient, "
                    "the request is not a duplicate, and the "
                    "requested leave duration complies with the policy."
                )


    # -----------------------------------------------------
    # ATTENDANCE CORRECTION
    # -----------------------------------------------------

    elif "attendance_exists" in validation_result:

        employee_exists = validation_result.get(
            "employee_exists"
        )

        attendance_exists = validation_result.get(
            "attendance_exists"
        )

        duplicate = validation_result.get(
            "duplicate"
        )

        within_limit = validation_result.get(
            "within_limit"
        )

        correction_type = employee_request.get(
            "correction_type",
            ""
        )

        reason = employee_request.get(
            "reason",
            ""
        )

        reason_lower = str(reason).lower()


        # -------------------------------------------------
        # EMPLOYEE DOES NOT EXIST
        # -------------------------------------------------

        if employee_exists is False:

            recommendation["recommendation"] = "Rejected"

            recommendation["reason"] = (
                "Employee does not exist in the Employee Master."
            )


        # -------------------------------------------------
        # ATTENDANCE RECORD DOES NOT EXIST
        # -------------------------------------------------

        elif attendance_exists is False:

            recommendation["recommendation"] = "Rejected"

            recommendation["reason"] = (
                "Attendance record does not exist for the requested date."
            )


        # -------------------------------------------------
        # OUTSIDE 3-DAY LIMIT / FUTURE DATE
        # -------------------------------------------------

        elif within_limit is False:

            recommendation["recommendation"] = "Rejected"

            recommendation["reason"] = (
                "Attendance correction request is outside the "
                "allowed 3-day limit or the attendance date is invalid."
            )


        # -------------------------------------------------
        # DUPLICATE
        # -------------------------------------------------

        elif duplicate is True:

            recommendation["recommendation"] = "Rejected"

            recommendation["reason"] = (
                "A duplicate attendance correction request already exists."
            )


        # -------------------------------------------------
        # ATTENDANCE DURING LEAVE → HUMAN REVIEW
        # -------------------------------------------------
        #
        # This works when validation_attendance.py returns
        # attendance_during_leave = True.
        #

        elif validation_result.get("attendance_during_leave") is True:

            recommendation["recommendation"] = "Needs Human Review"

            recommendation["reason"] = (
                "Attendance is recorded on a date associated with "
                "leave. The attendance and leave records require "
                "manual HR verification."
            )


        # -------------------------------------------------
        # OTHER EXCEPTIONAL SYSTEM ISSUES → HUMAN REVIEW
        # -------------------------------------------------

        elif (
            correction_type in [
                "Attendance System Failure",
                "Network Connectivity Issue",
                "Biometric Device Failure"
            ]
            or "biometric" in reason_lower
            or "system failure" in reason_lower
            or "network connectivity" in reason_lower
        ):

            recommendation["recommendation"] = (
                "Needs Human Review"
            )

            recommendation["reason"] = (
                "The attendance correction involves an exceptional "
                "system issue and requires manual HR verification."
            )


        # -------------------------------------------------
        # VALID ATTENDANCE CORRECTION
        # -------------------------------------------------

        else:

            recommendation["recommendation"] = "Approved"

            recommendation["reason"] = (
                "Employee exists, attendance record exists, "
                "the request is within the allowed 3-day limit, "
                "and the request is not a duplicate."
            )


    # -----------------------------------------------------
    # WFH REQUEST
    # -----------------------------------------------------

    elif "wfh_remaining" in validation_result:

        employee_exists = validation_result.get(
            "employee_exists"
        )

        duplicate = validation_result.get(
            "duplicate"
        )

        wfh_remaining = validation_result.get(
            "wfh_remaining"
        )

        if employee_exists is False:

            recommendation["recommendation"] = "Rejected"

            recommendation["reason"] = (
                "Employee does not exist in the Employee Master."
            )

        elif duplicate is True:

            recommendation["recommendation"] = "Rejected"

            recommendation["reason"] = (
                "A duplicate Work From Home request already exists."
            )

        elif wfh_remaining is None:

            recommendation["recommendation"] = "Needs Human Review"

            recommendation["reason"] = (
                "Remaining Work From Home balance could not be verified."
            )

        else:

            try:
                wfh_remaining_value = float(wfh_remaining)

            except (ValueError, TypeError):
                wfh_remaining_value = None


            if wfh_remaining_value is None:

                recommendation["recommendation"] = "Needs Human Review"

                recommendation["reason"] = (
                    "Remaining Work From Home balance could not be verified."
                )

            elif wfh_remaining_value <= 0:

                recommendation["recommendation"] = "Rejected"

                recommendation["reason"] = (
                    "The employee has no remaining Work From Home days."
                )

            else:

                recommendation["recommendation"] = "Approved"

                recommendation["reason"] = (
                    "Employee exists, WFH balance is available, "
                    "and the request is not a duplicate."
                )


    # -----------------------------------------------------
    # EMPLOYEE INFORMATION UPDATE
    # -----------------------------------------------------

    elif "employee_information" in validation_result:

        if validation_result.get("employee_exists") is False:

            recommendation["recommendation"] = "Rejected"

            recommendation["reason"] = (
                "Employee does not exist in the Employee Master."
            )


    # -----------------------------------------------------
    # GENERAL DUPLICATE SAFETY
    # -----------------------------------------------------

    if (
        "leave_balance" not in validation_result
        and "attendance_exists" not in validation_result
        and "wfh_remaining" not in validation_result
        and validation_result.get("duplicate") is True
    ):

        recommendation["recommendation"] = "Rejected"

        recommendation["reason"] = (
            "The request is a duplicate and has already been processed."
        )


    # -----------------------------------------------------
    # GENERAL EMPLOYEE SAFETY
    # -----------------------------------------------------

    if (
        "leave_balance" not in validation_result
        and "attendance_exists" not in validation_result
        and "wfh_remaining" not in validation_result
        and validation_result.get("employee_exists") is False
    ):

        recommendation["recommendation"] = "Rejected"

        recommendation["reason"] = (
            "Employee does not exist in the Employee Master."
        )

    # =====================================================
    # RETURN FINAL DECISION
    # =====================================================

    return json.dumps(
        recommendation,
        indent=4
    )
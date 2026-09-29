import json
import imap_reader
import parser
import prompt
import llm

from rag import search_policy
from recommendation import generate_recommendation
from human_review import insert_review
from database import insert_email_transaction,connect_db
from validation import validate_leave
from validation_wfh import validate_wfh
from validation_attendance import validate_attendance
from leave_transaction import insert_leave_transaction
from datetime import datetime
from leave_procedure import process_leave_request
from wfh_transaction import insert_wfh_transaction
from wfh_procedure import process_wfh_request
from attendance_procedure import process_attendance_request
from email_sender import send_reply_email

for email_id in imap_reader.email_ids:

    status, msg_data = imap_reader.mail.fetch(email_id, "(RFC822)")
    sender, subject, date, body = parser.parse_email(msg_data)

    final_prompt = prompt.build_prompt(body, date)
    response = llm.ask_llm(final_prompt)

    # Remove markdown if returned by the LLM
    response = response.replace("```json", "").replace("```", "").strip()

    try:
        result = json.loads(response)
        # ---------------------------------------
        # Default Office Timings for Attendance
        # ---------------------------------------

        if result.get("intent") == "Attendance Correction":

            correction_type = result.get("correction_type", "")

            if correction_type == "Missing Check-In":
                 result["check_in_time"] = "09:00"

            elif correction_type == "Missing Check-Out":
                 result["check_out_time"] = "18:00"
        print("Extracted Employee ID:", repr(result.get("employee_id", "")))
        print("Intent:", result.get("intent", ""))

        # Save email transaction
        message_id = insert_email_transaction(
            employee_id=result.get("employee_id", ""),
            subject=subject,
            body=body,
            received_datetime=date
        )

        print(f"Message ID : {message_id}")

        print("=" * 70)
        print("FROM    :", sender)
        print("SUBJECT :", subject)
        print("-" * 70)

        intent = result.get("intent", "")

        print("DATE =", date)

       
        # ===========================
        # RAG SEARCH
        # ===========================

        query = ""
        policy_type = ""

        if intent == "Leave Request":

            policy_type = "leave"

            leave_type = result.get("leave_type", "")

            query = f"""
            Retrieve the HR policy rules specifically for: {leave_type}.

            Employee Request Type: Leave Request
            Leave Type: {leave_type}
            Leave Days: {result.get('leave_days', '')}
            Reason: {result.get('reason', '')}
            Start Date: {result.get('start_date', '')}
            End Date: {result.get('end_date', '')}

            Focus ONLY on rules directly applicable to {leave_type}, including:
            - eligibility
            - entitlement
            - leave duration limits
            - leave balance validation
            - restrictions
            - approval conditions
            - rejection conditions

            Do NOT retrieve rules for unrelated leave categories such as
            Maternity Leave, Paternity Leave, Bereavement Leave,
            Leave Without Pay, Floater Leave, or Compensatory Off
            unless they are directly relevant to this request.
            """


        elif intent == "Work From Home Request":

            policy_type = "wfh"

            query = f"""
            Intent : {intent}
            Reason : {result.get('reason','')}
            From Date : {result.get('start_date','')}
            To Date : {result.get('end_date','')}
            """

        elif intent == "Attendance Correction":

            policy_type = "attendance"

            query = f"""
            Intent : {intent}
            Attendance Type : {result.get('correction_type','')}
            Attendance Date : {result.get('attendance_date','')}
            Reason : {result.get('reason','')}
            """

        elif intent == "Employee Information Update":

            policy_type = "employee_information"

            query = f"""
            Intent : {intent}
            Field : {result.get('field_to_update','')}
            New Value : {result.get('new_value','')}
            """

        policy_context = ""

        if query:

            policy_context = search_policy(
                query,
                policy_type
            )

            print("\n" + "=" * 80)
            print("RAG POLICY")
            print("=" * 80)
            print("Policy Type :", policy_type)
            print("=" * 80)
            print(policy_context)
            print("=" * 80)
        
            # =====================================
            # DATABASE VALIDATION
            # =====================================

            validation_result = {}

            if intent == "Leave Request":

               validation_result = validate_leave(
               employee_id=result.get("employee_id", ""),
               leave_type=result.get("leave_type", ""),
               start_date=result.get("start_date", ""),
               end_date=result.get("end_date", "")
            )
            elif intent == "Work From Home Request":

                validation_result = validate_wfh(
                    employee_id=result.get("employee_id", ""),
                    from_date=result.get("start_date", ""),
                    to_date=result.get("end_date", "")
            )
            elif intent == "Attendance Correction":

                print("DEBUG Attendance Request:", result)

                validation_result = validate_attendance(
                    employee_id=result.get("employee_id", ""),
                    attendance_date=result.get("attendance_date", ""),
                    correction_type=result.get("correction_type", ""),
                    message_id=message_id
            )

            if intent == "Leave Request":

               print("\n" + "=" * 80)
               print("DATABASE VALIDATION")
               print("=" * 80)

               print("Employee Exists :", validation_result["employee_exists"])
               print("Leave Balance   :", validation_result["leave_balance"])
               print("Duplicate Leave :", validation_result["duplicate"])
               print("working leave days:", validation_result["leave_days"])

               print("=" * 80)

            elif intent == "Work From Home Request":

               print("\n" + "=" * 80)
               print("DATABASE VALIDATION")
               print("=" * 80)
 
               print("Employee Exists :", validation_result["employee_exists"])
               print("WFH Used        :", validation_result["wfh_used"])
               print("WFH Remaining   :", validation_result["wfh_remaining"])
               print("Duplicate WFH   :", validation_result["duplicate"])

               print("=" * 80)

            elif intent == "Attendance Correction":

               print("\n" + "=" * 80)
               print("DATABASE VALIDATION")
               print("=" * 80)

               print("Employee Exists        :", validation_result["employee_exists"])
               print("Attendance Exists      :", validation_result["attendance_exists"])
               print("Duplicate Request      :", validation_result["duplicate"])
               print("Within 3 Days          :", validation_result["within_limit"])
               
               print("=" * 80)  

            if intent == "Leave Request":
                result["leave_days"] = validation_result["leave_days"]    

            employee_request = json.dumps(result, indent=4)

            recommendation = generate_recommendation(
                 employee_request,
                 policy_context,
                 validation_result
            )

            print("\n" + "=" * 80)
            print("AI RECOMMENDATION")
            print("=" * 80)
            print(recommendation)
            print("=" * 80)

        # ------------------------------------
        # Convert Recommendation JSON
        # ------------------------------------

        recommendation = recommendation.replace("```json", "").replace("```", "").strip()

        recommendation_data = json.loads(recommendation)

        rag_decision = recommendation_data.get("recommendation", "")
        rag_reason = recommendation_data.get("reason", "")

        # ------------------------------------
        # Update Email Processing Status
        # ------------------------------------

        if rag_decision == "Approved":
            processing_status = "Processed"
   
        elif rag_decision == "Rejected":
            processing_status = "Rejected"

        elif rag_decision == "Needs Human Review":
            processing_status = "Human Review"

        else:
            processing_status = "Pending"

        conn = connect_db()
        cursor = conn.cursor()
  
        cursor.execute("""
           UPDATE Email_Transaction
           SET Processing_Status = %s
           WHERE Message_ID = %s
        """, (
          processing_status,
          message_id
        ))

        conn.commit()

        cursor.close()
        conn.close()

        print(f" Email Processing Status: {processing_status}")

        if rag_decision == "Approved":

            if intent == "Leave Request":

               applied_date=datetime.strptime(
                   date,
                   "%a, %d %b %Y %H:%M:%S %z"
            ).strftime("%Y-%m-%d")

               insert_leave_transaction(
                 message_id=message_id,
                 employee_id=result.get("employee_id", ""),
                 leave_type=result.get("leave_type", ""),
                 start_date=result.get("start_date", ""),
                 end_date=result.get("end_date", ""),
                 reason=result.get("reason", ""),
                 applied_date=applied_date
                 
               )

               leave_processed =process_leave_request(
                  message_id=message_id,
                  employee_id=result.get("employee_id", ""),
                  leave_type=result.get("leave_type", ""),
                  start_date=result.get("start_date", ""),
                  end_date=result.get("end_date", ""),
                  reason=result.get("reason", ""),
                  received_datetime=applied_date
               )

               if leave_processed: 
                   print(" Leave Transaction Inserted")
               else:
                   print("leave request was not processed") 


            elif intent == "Work From Home Request":

              applied_date = datetime.strptime(
                  date,
                  "%a, %d %b %Y %H:%M:%S %z"
              ).strftime("%Y-%m-%d")

              insert_wfh_transaction(
                  message_id=message_id,
                  employee_id=result.get("employee_id", ""),
                  from_date=result.get("start_date", ""),
                  to_date=result.get("end_date", ""),
                  reason=result.get("reason", ""),
                  applied_date=applied_date
              )
              process_wfh_request(
                  message_id=message_id,
                  employee_id=result.get("employee_id", ""),
                  from_date=result.get("start_date", ""),
                  to_date=result.get("end_date", ""),
                  reason=result.get("reason", ""),
                  received_datetime=applied_date
              )

              print(" WFH Transaction Inserted")

            elif intent == "Attendance Correction":

              applied_date = datetime.strptime(
                    date,
                    "%a, %d %b %Y %H:%M:%S %z"
              ).strftime("%Y-%m-%d")

              process_attendance_request(
                   message_id=message_id,
                   employee_id=result.get("employee_id", ""),
                   attendance_date=result.get("attendance_date", ""),
                   correction_type=result.get("correction_type", ""),
                   check_in_time=result.get("check_in_time", None),
                   check_out_time=result.get("check_out_time", None),
                   reason=result.get("reason", ""),
                   received_date=applied_date
              )

              print(" Attendance Correction Processed")

        # ------------------------------------
        # Save Human Review
        # ------------------------------------
        if rag_decision == "Needs Human Review":
        

          if intent == "Leave Request":
              request_type = "Leave"

          elif intent == "Work From Home Request":
              request_type = "WFH"

          elif intent == "Attendance Correction":
              request_type = "Attendance"

          elif intent == "Employee Information Update":
              request_type = "Employee Details"

          else:
              request_type = ""

          review_id = insert_review(
            message_id=message_id,
            employee_id=result.get("employee_id", ""),
            request_type=request_type,
            rag_decision=rag_decision,
            rag_reason=rag_reason
          )

          print(f"Review ID : {review_id}")

        # ------------------------------------
        # Send Final Reply Email
        # ------------------------------------

        employee_name = result.get("employee_name", "Employee")

        if intent == "Leave Request":
            request_type = "Leave"

        elif intent == "Work From Home Request":
            request_type = "Work From Home"

        elif intent == "Attendance Correction":
            request_type = "Attendance Correction"

        elif intent == "Employee Information Update":
            request_type = "Employee Information Update"

        else:
            request_type = "HR"

        email_sent = send_reply_email(
            employee_email=sender,
            subject=subject,
            employee_name=employee_name,
            request_type=request_type,
            decision=rag_decision,
            reason=rag_reason
        )

        if email_sent:
            print(" Final reply email sent successfully")
        else:
            print(" Final reply email could not be sent")
            

        # Print extracted JSON
        if intent == "Leave Request":

            print("Intent         :", intent)
            print("Employee ID    :", result.get("employee_id", ""))
            print("Employee Name  :", result.get("employee_name", ""))
            print("Leave Type     :", result.get("leave_type", ""))
            print("Leave Days     :", result.get("leave_days", ""))
            print("Start Date     :", result.get("start_date", ""))
            print("End Date       :", result.get("end_date", ""))
            print("Reason         :", result.get("reason", ""))

        elif intent == "Work From Home Request":

            print("Intent         :", intent)
            print("Employee ID    :", result.get("employee_id", ""))
            print("Employee Name  :", result.get("employee_name", ""))
            print("Start Date     :", result.get("start_date", ""))
            print("End Date       :", result.get("end_date", ""))
            print("Reason         :", result.get("reason", ""))

        elif intent == "Attendance Correction":

            print("Intent             :", intent)
            print("Employee ID        :", result.get("employee_id", ""))
            print("Employee Name      :", result.get("employee_name", ""))
            print("Attendance Date    :", result.get("attendance_date", ""))
            print("Correction Type    :", result.get("correction_type", ""))
            print("Reason             :", result.get("reason", ""))

        elif intent == "Employee Information Update":

            print("Intent             :", intent)
            print("Employee ID        :", result.get("employee_id", ""))
            print("Employee Name      :", result.get("employee_name", ""))
            print("Field to Update    :", result.get("field_to_update", ""))
            print("Old Value          :", result.get("old_value", ""))
            print("New Value          :", result.get("new_value", ""))
            print("Reason             :", result.get("reason", ""))

        elif intent == "Unsupported Request":

            print("Intent :", intent)
            print("This email is not related to any supported HR operation.")

        else:

            print("Unknown intent received:")
            print(result)

        print("=" * 70)

    except json.JSONDecodeError:

        print("=" * 70)
        print("FROM    :", sender)
        print("SUBJECT :", subject)
        print("-" * 70)
        print("Error: Invalid JSON returned by the LLM.")
        print(response)
        print("=" * 70)
from database import connect_db, generate_review_id


def insert_review(
    message_id,
    employee_id,
    request_type,
    rag_decision,
    rag_reason
):

    conn = connect_db()
    cursor = conn.cursor()

    review_id = generate_review_id()

    query = """
    INSERT INTO Human_Review
    (
        Review_ID,
        Message_ID,
        Employee_ID,
        Request_Type,
        RAG_Decision,
        RAG_Reason,
        Human_Decision,
        Final_Decision,
        Reviewed_By,
        Review_Date,
        Status
    )
    VALUES
    (
        %s,
        %s,
        %s,
        %s,
        %s,
        %s,
        NULL,
        'Pending',
        NULL,
        NULL,
        'Pending'
    )
    """

    values = (
        review_id,
        message_id,
        employee_id,
        request_type,
        rag_decision,
        rag_reason
    )

    cursor.execute(query, values)

    conn.commit()

    cursor.close()
    conn.close()

    print(f"✅ Human Review inserted successfully. Review ID: {review_id}")

    return review_id
from database import db


async def delete_course_related_data(course_id: str):
    await db.lessons.delete_many({"course_id": course_id})
    await db.quizzes.delete_many({"course_id": course_id})
    await db.enrollments.delete_many({"course_id": course_id})
    await db.certificates.delete_many({"course_id": course_id})
    await db.forum_posts.delete_many({"course_id": course_id})
    await db.chat_messages.delete_many({"course_id": course_id})
    await db.payment_transactions.delete_many({"course_id": course_id})
    await db.quiz_attempts.delete_many({"course_id": course_id})

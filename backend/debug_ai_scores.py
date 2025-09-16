#!/usr/bin/env python3
"""
Debug script to analyze AI score data flow and positioning
"""
import sys
import json
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def get_database_connection():
    """Get database connection"""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URL not found in environment")
        return None

    try:
        engine = create_engine(database_url)
        Session = sessionmaker(bind=engine)
        return Session()
    except Exception as e:
        print(f"❌ Failed to connect to database: {e}")
        return None


def analyze_assignment_ai_scores(assignment_id):
    """Analyze AI scores for a specific assignment"""
    session = get_database_connection()
    if not session:
        return

    try:
        print(f"🔍 Analyzing Assignment ID: {assignment_id}")
        print("=" * 60)

        # Get assignment details
        assignment_query = text(
            """
            SELECT a.id, a.title, a.created_at,
                   JSON_LENGTH(a.activities) as activity_count
            FROM assignments a
            WHERE a.id = :assignment_id
        """
        )
        assignment = session.execute(
            assignment_query, {"assignment_id": assignment_id}
        ).fetchone()

        if not assignment:
            print(f"❌ Assignment {assignment_id} not found")
            return

        print(f"📋 Assignment: {assignment.title}")
        print(f"📊 Activity Count: {assignment.activity_count}")
        print(f"📅 Created: {assignment.created_at}")
        print()

        # Get activities with detailed structure
        activities_query = text(
            """
            SELECT JSON_EXTRACT(activities, '$') as activities_data
            FROM assignments
            WHERE id = :assignment_id
        """
        )
        activities_result = session.execute(
            activities_query, {"assignment_id": assignment_id}
        ).fetchone()

        if activities_result and activities_result.activities_data:
            activities = json.loads(activities_result.activities_data)

            print("🏗️ ACTIVITY STRUCTURE ANALYSIS:")
            print("-" * 40)

            global_index = 0
            for i, activity in enumerate(activities):
                print(f"Activity {i+1}: {activity.get('title', 'Untitled')}")
                print(f"  Type: {activity.get('type', 'Unknown')}")

                items = activity.get("items", [])
                print(f"  Items Count: {len(items)}")

                # Analyze items structure
                for j, item in enumerate(items):
                    item_text = item.get("text", item.get("question", "No text"))
                    print(
                        f"    Item {j} (Global Index {global_index}): {item_text[:50]}..."
                    )
                    global_index += 1

                # Check for AI scores
                ai_scores = activity.get("ai_scores", {})
                if ai_scores:
                    scores_json = json.dumps(ai_scores, indent=4)
                    print(f"  🤖 AI Scores Present: {scores_json}")
                else:
                    print("  🚫 No AI Scores")

                print()

        # Get student attempts and AI assessments
        attempts_query = text(
            """
            SELECT sa.id, sa.student_id, sa.activity_index, sa.item_index,
                   sa.ai_assessment, sa.created_at,
                   s.username
            FROM student_attempts sa
            JOIN students s ON sa.student_id = s.id
            WHERE sa.assignment_id = :assignment_id
            AND sa.ai_assessment IS NOT NULL
            ORDER BY sa.created_at DESC
        """
        )

        attempts = session.execute(
            attempts_query, {"assignment_id": assignment_id}
        ).fetchall()

        print("🎯 AI ASSESSMENT ATTEMPTS:")
        print("-" * 40)

        if not attempts:
            print("❌ No AI assessments found for this assignment")
        else:
            for attempt in attempts:
                print(f"Student: {attempt.username}")
                print(f"  Activity Index: {attempt.activity_index}")
                print(f"  Item Index: {attempt.item_index}")
                if attempt.ai_assessment:
                    assessment_data = json.loads(attempt.ai_assessment)
                    assessment_json = json.dumps(assessment_data, indent=2)
                    print(f"  Assessment: {assessment_json}")
                else:
                    print("  Assessment: None")
                print(f"  Created: {attempt.created_at}")
                print()

        # Calculate expected global indices
        print("🧮 GLOBAL INDEX CALCULATION:")
        print("-" * 40)

        if activities_result and activities_result.activities_data:
            activities = json.loads(activities_result.activities_data)
            global_index = 0

            for i, activity in enumerate(activities):
                items = activity.get("items", [])
                start_index = global_index
                end_index = global_index + len(items) - 1

                print(
                    f"Activity {i}: Global indices {start_index} to {end_index} ({len(items)} items)"
                )

                # Check if any AI scores should map to this range
                for attempt in attempts:
                    if attempt.activity_index == i:
                        expected_global = start_index + attempt.item_index
                        print(
                            f"  📍 AI Score at activity {i}, item {attempt.item_index} → Global index {expected_global}"
                        )

                global_index += len(items)

    except Exception as e:
        print(f"❌ Error analyzing assignment: {e}")
        import traceback

        traceback.print_exc()
    finally:
        session.close()


def main():
    if len(sys.argv) != 2:
        print("Usage: python debug_ai_scores.py <assignment_id>")
        sys.exit(1)

    try:
        assignment_id = int(sys.argv[1])
        analyze_assignment_ai_scores(assignment_id)
    except ValueError:
        print("❌ Assignment ID must be a number")
        sys.exit(1)


if __name__ == "__main__":
    main()

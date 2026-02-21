"""
E2E Test: Org Points Deduction via Speech Assessment

Tests the full flow:
  1. Teacher login -> check org points BEFORE
  2. Student login -> get assignment -> get progress_id
  3. Generate WAV audio -> POST /api/speech/assess
  4. Teacher login -> check org points AFTER
  5. Compare BEFORE / AFTER

Preview Backend URL (configurable via env):
  PREVIEW_BACKEND_URL=https://duotopia-preview-issue-208-backend-b2ovkkgl6a-de.a.run.app

Run:
  python backend/tests/e2e/test_org_points_e2e.py
"""

import io
import math
import os
import struct
import sys
import time
import wave

import requests

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

BACKEND_URL = os.environ.get(
    "PREVIEW_BACKEND_URL",
    "https://duotopia-preview-issue-208-backend-b2ovkkgl6a-de.a.run.app",
)

# Teacher credentials (org owner)
TEACHER_EMAIL = os.environ.get("TEACHER_EMAIL", "owner@duotopia.com")
TEACHER_PASSWORD = os.environ.get("SEED_DEFAULT_PASSWORD", "demo123")

# Organization
ORG_ID = "21a8a0c7-a5e3-4799-8336-fbb2cf1de91a"

# Student credentials (student in Lion classroom under 南港分校)
STUDENT_ID = int(os.environ.get("STUDENT_ID", "44"))
STUDENT_PASSWORD = os.environ.get("STUDENT_PASSWORD", "20100115")  # birthdate YYYYMMDD

# Reference text for speech assessment
REFERENCE_TEXT = "hello"

# Timeout for HTTP requests (seconds)
HTTP_TIMEOUT = 30


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def banner(step: int, msg: str):
    print(f"\n{'='*60}")
    print(f"  STEP {step}: {msg}")
    print(f"{'='*60}")


def login_with_retry(url: str, payload: dict, label: str, max_retries: int = 3):
    """Login with retry logic for rate limiting (3/min)."""
    for attempt in range(1, max_retries + 1):
        print(f"  [{label}] Attempt {attempt}/{max_retries} ...")
        try:
            resp = requests.post(url, json=payload, timeout=HTTP_TIMEOUT)
        except requests.exceptions.RequestException as e:
            print(f"  [{label}] Network error: {e}")
            if attempt < max_retries:
                print(f"  [{label}] Waiting 25s before retry ...")
                time.sleep(25)
                continue
            raise

        if resp.status_code == 200:
            data = resp.json()
            token = data.get("access_token")
            user = data.get("user", {})
            print(
                f"  [{label}] Login OK  user={user.get('name', user.get('email', '?'))}"
            )
            return token, data

        if resp.status_code == 429:
            print(f"  [{label}] Rate limited (429). Waiting 25s ...")
            time.sleep(25)
            continue

        # Other error
        print(f"  [{label}] HTTP {resp.status_code}: {resp.text[:300]}")
        if attempt < max_retries:
            time.sleep(5)
            continue
        resp.raise_for_status()

    raise RuntimeError(f"[{label}] All {max_retries} login attempts failed")


def generate_wav_audio(duration_sec: float = 2.0, freq_hz: float = 440.0) -> bytes:
    """Generate a valid WAV file with a sine wave (16-bit PCM, 16 kHz, mono)."""
    sample_rate = 16000
    n_samples = int(sample_rate * duration_sec)
    amplitude = 16000  # ~50% of int16 max

    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(sample_rate)

        frames = bytearray()
        for i in range(n_samples):
            sample = int(amplitude * math.sin(2 * math.pi * freq_hz * i / sample_rate))
            frames.extend(struct.pack("<h", sample))

        wf.writeframes(bytes(frames))

    return buf.getvalue()


# ---------------------------------------------------------------------------
# Steps
# ---------------------------------------------------------------------------


def step1_teacher_login() -> str:
    """Login as teacher and return access token."""
    banner(1, "Login as teacher")
    token, _ = login_with_retry(
        url=f"{BACKEND_URL}/api/auth/teacher/login",
        payload={"email": TEACHER_EMAIL, "password": TEACHER_PASSWORD},
        label="Teacher",
    )
    return token


def step2_check_org_points(teacher_token: str, label: str = "BEFORE") -> dict:
    """Check org points balance. Returns the full response dict."""
    banner(2 if label == "BEFORE" else 8, f"Check org points ({label})")
    headers = {"Authorization": f"Bearer {teacher_token}"}
    resp = requests.get(
        f"{BACKEND_URL}/api/organizations/{ORG_ID}/points",
        headers=headers,
        timeout=HTTP_TIMEOUT,
    )
    print(f"  HTTP {resp.status_code}")
    if resp.status_code != 200:
        print(f"  Response: {resp.text[:500]}")
        resp.raise_for_status()

    data = resp.json()
    print(f"  total_points   = {data.get('total_points')}")
    print(f"  used_points    = {data.get('used_points')}")
    print(f"  remaining      = {data.get('remaining_points')}")
    return data


def step3_find_assignment(teacher_token: str) -> dict:
    """
    Find an assignment in the Lion classroom that belongs to 南港分校.

    Returns info dict with school_id, classroom_id, etc.
    """
    banner(3, "Find assignment in Lion classroom (南港分校)")

    headers = {"Authorization": f"Bearer {teacher_token}"}

    # List schools under the org
    resp = requests.get(
        f"{BACKEND_URL}/api/schools",
        headers=headers,
        timeout=HTTP_TIMEOUT,
    )
    print(f"  GET /api/schools -> HTTP {resp.status_code}")
    if resp.status_code == 200:
        schools = resp.json()
        if isinstance(schools, list):
            for s in schools:
                name = s.get("display_name") or s.get("name", "")
                print(f"    School: id={s.get('id')}  name={name}")
        elif isinstance(schools, dict) and "items" in schools:
            for s in schools["items"]:
                name = s.get("display_name") or s.get("name", "")
                print(f"    School: id={s.get('id')}  name={name}")
    else:
        print(f"  Schools response: {resp.text[:300]}")

    # Try to get classrooms from the dashboard or teacher classrooms endpoint
    resp2 = requests.get(
        f"{BACKEND_URL}/api/classrooms",
        headers=headers,
        timeout=HTTP_TIMEOUT,
    )
    print(f"  GET /api/classrooms -> HTTP {resp2.status_code}")
    if resp2.status_code == 200:
        classrooms = resp2.json()
        if isinstance(classrooms, list):
            for c in classrooms:
                print(f"    Classroom: id={c.get('id')}  name={c.get('name')}")
        elif isinstance(classrooms, dict):
            for c in classrooms.get("items", classrooms.get("classrooms", [])):
                print(f"    Classroom: id={c.get('id')}  name={c.get('name')}")
    else:
        print(f"  Classrooms response: {resp2.text[:300]}")

    # We'll discover the assignment from the student side in step 5
    return {}


def step4_student_login() -> str:
    """Login as student and return access token."""
    banner(4, f"Login as student (id={STUDENT_ID})")

    # Wait for rate limiter cooldown from teacher login
    print("  Waiting 22s for rate limiter cooldown ...")
    time.sleep(22)

    token, data = login_with_retry(
        url=f"{BACKEND_URL}/api/auth/student/login",
        payload={"id": STUDENT_ID, "password": STUDENT_PASSWORD},
        label="Student",
    )
    user = data.get("user", {})
    print(f"  Student name: {user.get('name')}")
    print(f"  School: {user.get('school_name')}")
    print(f"  Org: {user.get('organization_name')}")
    return token


def step5_get_assignment_and_progress(student_token: str) -> dict:
    """
    Get student's assignments, find one with speech content,
    and return assignment_id + progress_id.
    """
    banner(5, "Get student assignments and progress")

    headers = {"Authorization": f"Bearer {student_token}"}

    # Get student assignments
    resp = requests.get(
        f"{BACKEND_URL}/api/students/assignments",
        headers=headers,
        timeout=HTTP_TIMEOUT,
    )
    print(f"  GET /api/students/assignments -> HTTP {resp.status_code}")
    if resp.status_code != 200:
        print(f"  Response: {resp.text[:500]}")
        resp.raise_for_status()

    assignments = resp.json()
    if not assignments:
        print("  WARNING: No assignments found for this student!")
        print("  Will try to proceed with a dummy progress_id ...")
        return {"assignment_id": None, "progress_id": None}

    print(f"  Found {len(assignments)} assignment(s)")
    for a in assignments:
        print(
            f"    id={a['id']}  title={a.get('title', '?')[:40]}  status={a.get('status')}"
        )

    # Try each assignment to find one with activities (speech content)
    for assignment in assignments:
        sa_id = assignment["id"]
        resp2 = requests.get(
            f"{BACKEND_URL}/api/students/assignments/{sa_id}/activities",
            headers=headers,
            timeout=HTTP_TIMEOUT,
        )
        print(
            f"\n  GET /api/students/assignments/{sa_id}/activities -> HTTP {resp2.status_code}"
        )
        if resp2.status_code != 200:
            print(f"    Response: {resp2.text[:200]}")
            continue

        activities_data = resp2.json()
        activities = activities_data.get("activities", [])
        practice_mode = activities_data.get("practice_mode")
        print(f"    practice_mode={practice_mode}  activities_count={len(activities)}")

        # For speech assessment we need a reading_assessment type activity
        # or we just need any progress_id
        for act in activities:
            act_type = act.get("type", "")
            act_id = act.get(
                "id"
            )  # This is the StudentContentProgress.id = progress_id
            items = act.get("items", [])
            print(f"    Activity: id={act_id}  type={act_type}  items={len(items)}")

            if act_type in ("reading_assessment", "reading") and act_id and act_id > 0:
                # Found a suitable activity!
                progress_id = act_id

                # Get the reference text from first item if available
                ref_text = REFERENCE_TEXT
                if items:
                    first_text = items[0].get("text", "")
                    if first_text:
                        ref_text = first_text
                        print(f"    Using reference_text from item: '{ref_text[:60]}'")

                result = {
                    "assignment_id": sa_id,  # StudentAssignment.id
                    "progress_id": progress_id,  # StudentContentProgress.id
                    "reference_text": ref_text,
                }
                print(f"\n  Selected: assignment_id={sa_id}, progress_id={progress_id}")
                return result

    # If no reading_assessment found, use first assignment with first activity
    if assignments:
        sa_id = assignments[0]["id"]
        resp2 = requests.get(
            f"{BACKEND_URL}/api/students/assignments/{sa_id}/activities",
            headers=headers,
            timeout=HTTP_TIMEOUT,
        )
        if resp2.status_code == 200:
            activities_data = resp2.json()
            activities = activities_data.get("activities", [])
            if activities and activities[0].get("id", 0) > 0:
                result = {
                    "assignment_id": sa_id,
                    "progress_id": activities[0]["id"],
                    "reference_text": REFERENCE_TEXT,
                }
                print(
                    f"\n  Fallback: assignment_id={sa_id}, progress_id={activities[0]['id']}"
                )
                return result

    print("\n  WARNING: No suitable activity found. Using placeholder values.")
    return {
        "assignment_id": None,
        "progress_id": None,
        "reference_text": REFERENCE_TEXT,
    }


def step6_generate_audio() -> bytes:
    """Generate a valid WAV audio file."""
    banner(6, "Generate WAV audio file")
    wav_data = generate_wav_audio(duration_sec=2.0, freq_hz=440.0)
    print(f"  Generated WAV: {len(wav_data)} bytes ({len(wav_data)/1024:.1f} KB)")
    print(f"  Format: 16-bit PCM, 16000 Hz, mono, ~2 seconds")
    return wav_data


def step7_speech_assess(
    student_token: str,
    wav_data: bytes,
    progress_id: int,
    assignment_id: int,
    reference_text: str,
) -> dict:
    """Call speech assessment endpoint."""
    banner(7, "Call speech assessment")

    if progress_id is None or assignment_id is None:
        print("  SKIP: No valid progress_id or assignment_id available.")
        print("  The student may not have any speech assignments.")
        return {"skipped": True}

    headers = {"Authorization": f"Bearer {student_token}"}

    # Prepare multipart form data
    files = {
        "audio_file": ("test_audio.wav", wav_data, "audio/wav"),
    }
    data = {
        "reference_text": reference_text,
        "progress_id": str(progress_id),
        "assignment_id": str(assignment_id),
    }

    print(f"  POST /api/speech/assess")
    print(f"    reference_text = '{reference_text[:60]}'")
    print(f"    progress_id    = {progress_id}")
    print(f"    assignment_id  = {assignment_id}")
    print(f"    audio_file     = test_audio.wav ({len(wav_data)} bytes)")

    try:
        resp = requests.post(
            f"{BACKEND_URL}/api/speech/assess",
            headers=headers,
            files=files,
            data=data,
            timeout=60,  # Speech assessment can take time
        )
    except requests.exceptions.Timeout:
        print("  TIMEOUT: Speech assessment request timed out after 60s")
        return {"error": "timeout", "status_code": None}
    except requests.exceptions.RequestException as e:
        print(f"  ERROR: Network error: {e}")
        return {"error": str(e), "status_code": None}

    print(f"  HTTP {resp.status_code}")

    if resp.status_code == 200:
        result = resp.json()
        print(f"  SUCCESS!")
        print(f"    accuracy_score      = {result.get('accuracy_score')}")
        print(f"    fluency_score       = {result.get('fluency_score')}")
        print(f"    completeness_score  = {result.get('completeness_score')}")
        print(f"    pronunciation_score = {result.get('pronunciation_score')}")
        return result

    # Error responses
    try:
        error_data = resp.json()
    except Exception:
        error_data = resp.text[:500]

    print(f"  Response: {error_data}")

    if resp.status_code == 400:
        detail = (
            error_data.get("detail", "")
            if isinstance(error_data, dict)
            else str(error_data)
        )
        if "No speech could be recognized" in str(detail):
            print("  NOTE: Azure could not recognize speech in the generated audio.")
            print("  This is expected for a simple sine wave. The important thing is")
            print("  whether the code REACHED the assessment point (it did).")
        elif "Audio format" in str(detail):
            print("  NOTE: Audio format issue. Check ALLOWED_AUDIO_FORMATS.")
    elif resp.status_code == 402:
        print(
            "  NOTE: Points/quota limit exceeded (402). This means deduction logic is working!"
        )
    elif resp.status_code == 503:
        print("  NOTE: Azure Speech API error or timeout (503).")

    return {
        "error": error_data,
        "status_code": resp.status_code,
    }


def step9_print_results(before: dict, after: dict, assess_result: dict):
    """Print comparison of BEFORE and AFTER points."""
    banner(9, "RESULTS SUMMARY")

    used_before = before.get("used_points", "?")
    used_after = after.get("used_points", "?")
    remaining_before = before.get("remaining_points", "?")
    remaining_after = after.get("remaining_points", "?")

    print(f"  Organization: {ORG_ID}")
    print(f"  Total points: {before.get('total_points', '?')}")
    print()
    print(f"  {'':20s} {'BEFORE':>10s}  {'AFTER':>10s}  {'DIFF':>10s}")
    print(f"  {'-'*55}")

    if isinstance(used_before, (int, float)) and isinstance(used_after, (int, float)):
        diff_used = used_after - used_before
        diff_remaining = remaining_after - remaining_before
        print(
            f"  {'used_points':20s} {used_before:>10}  {used_after:>10}  {diff_used:>+10}"
        )
        print(
            f"  {'remaining_points':20s} {remaining_before:>10}  {remaining_after:>10}  {diff_remaining:>+10}"
        )
        print()
        if diff_used > 0:
            print(f"  *** POINTS DEDUCTED: {diff_used} points ***")
            print(f"  Org points deduction is WORKING!")
        elif diff_used == 0:
            print(f"  *** NO CHANGE in points ***")
            if assess_result.get("skipped"):
                print(f"  (Speech assessment was skipped - no assignment found)")
            elif assess_result.get("error"):
                print(f"  (Speech assessment returned an error)")
                print(f"  Error: {assess_result.get('error')}")
            else:
                print(f"  Check if deduction logic was triggered.")
        else:
            print(f"  *** UNEXPECTED: Points decreased by {abs(diff_used)}! ***")
    else:
        print(f"  {'used_points':20s} {used_before!s:>10s}  {used_after!s:>10s}")
        print(
            f"  {'remaining_points':20s} {remaining_before!s:>10s}  {remaining_after!s:>10s}"
        )

    print()

    # Assessment result summary
    print(f"  Speech Assessment Result:")
    if assess_result.get("accuracy_score") is not None:
        print(f"    Status: SUCCESS")
        print(f"    Accuracy: {assess_result.get('accuracy_score')}")
    elif assess_result.get("skipped"):
        print(f"    Status: SKIPPED (no assignment)")
    elif assess_result.get("error"):
        print(f"    Status: ERROR ({assess_result.get('status_code', 'N/A')})")
        error = assess_result.get("error", "")
        if isinstance(error, dict):
            detail = error.get("detail", error)
            print(f"    Detail: {str(detail)[:200]}")
        else:
            print(f"    Detail: {str(error)[:200]}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    print("=" * 60)
    print("  ORG POINTS DEDUCTION E2E TEST")
    print(f"  Backend: {BACKEND_URL}")
    print(f"  Teacher: {TEACHER_EMAIL}")
    print(f"  Student: id={STUDENT_ID}")
    print(f"  Org:     {ORG_ID}")
    print("=" * 60)

    # Step 1: Teacher login
    teacher_token = step1_teacher_login()

    # Step 2: Check points BEFORE
    points_before = step2_check_org_points(teacher_token, "BEFORE")

    # Step 3: Explore assignments (informational)
    step3_find_assignment(teacher_token)

    # Step 4: Student login (wait for rate limit cooldown)
    student_token = step4_student_login()

    # Step 5: Get assignment and progress_id
    assignment_info = step5_get_assignment_and_progress(student_token)
    progress_id = assignment_info.get("progress_id")
    assignment_id = assignment_info.get("assignment_id")
    reference_text = assignment_info.get("reference_text", REFERENCE_TEXT)

    # Step 6: Generate audio
    wav_data = step6_generate_audio()

    # Step 7: Call speech assessment
    assess_result = step7_speech_assess(
        student_token=student_token,
        wav_data=wav_data,
        progress_id=progress_id,
        assignment_id=assignment_id,
        reference_text=reference_text,
    )

    # Step 8: Check points AFTER (need teacher token again)
    # Re-login as teacher to check points (student token won't work)
    banner(8, "Re-login as teacher to check points AFTER")
    print("  Waiting 22s for rate limiter cooldown ...")
    time.sleep(22)
    teacher_token2 = step1_teacher_login()
    points_after = step2_check_org_points(teacher_token2, "AFTER")

    # Step 9: Results
    step9_print_results(points_before, points_after, assess_result)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nAborted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nFATAL ERROR: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)

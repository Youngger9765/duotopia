# Bug 240 Root Cause Report

## Issue

https://github.com/Youngger9765/duotopia/issues/240

## Summary

Institution batch import fails and the dialog goes blank after clicking "import". The backend returns 422 because the request is matched to the wrong route. The frontend then surfaces an "Unknown error" and React crashes due to an object being rendered as a child.

## Evidence

- Request URL: `/api/schools/{school_id}/students/batch-import`
- Status: 422
- Response body:

```json
{
  "detail": [
    {
      "type": "int_parsing",
      "loc": ["path", "student_id"],
      "msg": "Input should be a valid integer, unable to parse string as an integer",
      "input": "batch-import",
      "url": "https://errors.pydantic.dev/2.5/v/int_parsing"
    }
  ]
}
```

## Root Cause

In [backend/routers/student_schools.py](../../backend/routers/student_schools.py#L340-L430), the POST route `/api/schools/{school_id}/students/{student_id}` is declared before the batch import route in [backend/routers/student_schools.py](../../backend/routers/student_schools.py#L560-L740). FastAPI matches the first route and attempts to parse `batch-import` as `student_id`, producing the 422 error.

The teacher batch import uses a different endpoint and router, so it does not conflict.

## Impact

- Institution batch import fails consistently.
- The UI crashes because the error handler tries to render a non-string error payload.

## Recommended Fix

1. Move `/api/schools/{school_id}/students/batch-import` above `/api/schools/{school_id}/students/{student_id}` in [backend/routers/student_schools.py](../../backend/routers/student_schools.py).
2. Harden frontend error handling to stringify non-string `detail` responses to avoid React error #31.

## Verification Steps

- Re-test POST `/api/schools/{school_id}/students/batch-import` with valid payload.
- Confirm import succeeds and UI does not crash.

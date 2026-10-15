"""Translate an authenticated/demo request into the application user identity."""

from apps.core.application.dtos import DemoSessionInput


def request_identity(request, use_cases) -> tuple[int, str]:
    """Return ``(user_id, email)`` without exposing ORM users to a view."""
    session_id = request.headers.get("X-Session-ID")
    if session_id:
        demo_user = use_cases["get_or_create_user"].execute(
            DemoSessionInput(session_id=session_id)
        )
        return demo_user.user_id, demo_user.email

    user = request.user
    return user.pk, getattr(user, "email", "")

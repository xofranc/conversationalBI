from dataclasses import replace
from datetime import date, datetime, timedelta, timezone

import pytest

from apps.core.application.dtos import DemoDatasetDTO, DemoSessionInput
from apps.core.application.use_cases import (
    CleanupDemoSession,
    CleanupExpiredDemoSessions,
    GetOrCreateDemoSession,
    GetOrCreateDemoUser,
    ListDemoSessionDatasets,
)
from apps.core.domain.entities import DEMO_SESSION_TTL, DemoSession
from apps.core.domain.value_objects import SessionIdentifier
from apps.dataset.domain.entities import Dataset
from apps.project_status.application.use_cases import (
    GetProjectStatus,
    ListProjectModules,
    ListProjectPhases,
)
from apps.project_status.domain.entities import (
    ProjectModule,
    ProjectModuleStatus,
    ProjectPhase,
    ProjectPhaseStatus,
)
from apps.users.application.dtos import (
    AuthenticateInput,
    CanAccessDatasetInput,
    GetProfileInput,
    GetQuotaInput,
    UpdateProfileInput,
)
from apps.users.application.use_cases import (
    AuthenticateExternalIdentity,
    CanAccessDataset,
    GetProfile,
    GetQuota,
    IncrementQueryUsage,
    UpdateProfile,
)
from apps.users.domain.entities import Profile, User
from apps.users.domain.exceptions import InvalidPhoneNumber
from apps.users.domain.value_objects import EmailAddress, PhoneNumber


class ProfileMemory:
    def __init__(self, profiles=(), phones=()):
        self.profiles = {profile.user_id: profile for profile in profiles}
        self.phones = set(phones)
        self.increments = []

    def get_by_user_id(self, user_id):
        return self.profiles.get(user_id)

    def phone_number_exists(self, phone_number, *, excluding_profile_id=None):
        return str(phone_number) in self.phones and not any(
            profile.id == excluding_profile_id and str(profile.phone_number) == str(phone_number)
            for profile in self.profiles.values()
        )

    def save(self, profile):
        profile = profile if profile.id is not None else replace(profile, id=profile.user_id + 100)
        self.profiles[profile.user_id] = profile
        return profile

    def increment_query_count(self, user_id):
        self.increments.append(user_id)
        profile = self.profiles.get(user_id, Profile(user_id=user_id))
        self.profiles[user_id] = profile.increment_query_count()


def test_profile_get_creates_default_and_update_changes_only_requested_fields():
    profiles = ProfileMemory()
    created = GetProfile(profiles).execute(GetProfileInput(7))
    assert (created.user_id, created.bio, created.phone_number) == (7, "", None)

    profiles.profiles[7] = Profile(user_id=7, id=107, bio="old", phone_number=PhoneNumber("1112223333"), entry_date=date(2020, 1, 1))
    updated = UpdateProfile(profiles).execute(UpdateProfileInput(
        user_id=7, bio="new", update_bio=True,
    ))
    assert (updated.bio, updated.phone_number, updated.entry_date) == ("new", "1112223333", date(2020, 1, 1))
    phone_cleared = UpdateProfile(profiles).execute(UpdateProfileInput(
        user_id=7, phone_number="", update_phone_number=True,
    ))
    assert phone_cleared.phone_number is None


def test_profile_update_enforces_phone_validity_and_uniqueness():
    profiles = ProfileMemory(phones={"1234567890"})
    with pytest.raises(InvalidPhoneNumber, match="exactamente 10"):
        UpdateProfile(profiles).execute(UpdateProfileInput(1, phone_number="123", update_phone_number=True))
    assert profiles.profiles == {}  # validation happens before repository persistence
    with pytest.raises(ValueError, match="ya está registrado"):
        UpdateProfile(profiles).execute(UpdateProfileInput(1, phone_number="1234567890", update_phone_number=True))
    assert profiles.profiles == {}


def test_profile_update_accepts_valid_phone_and_birth_date_without_overwriting_other_fields():
    profiles = ProfileMemory([Profile(user_id=5, id=105, bio="kept")])
    updated = UpdateProfile(profiles).execute(UpdateProfileInput(
        user_id=5, phone_number="5556667777", birth_date=date(1995, 8, 9),
        update_phone_number=True, update_birth_date=True,
    ))
    assert (updated.bio, updated.phone_number, updated.birth_date) == (
        "kept", "5556667777", date(1995, 8, 9),
    )
    replaced = UpdateProfile(profiles).execute(UpdateProfileInput(
        user_id=5, phone_number="5556667777", update_phone_number=True,
    ))
    assert replaced.phone_number == "5556667777"  # editing one's own number is allowed


def test_quota_is_informational_even_at_limit_and_missing_profile_is_unavailable():
    profiles = ProfileMemory([Profile(user_id=4, query_count=9, query_limit=9)])
    assert GetQuota(profiles).execute(GetQuotaInput(4)).available is False
    assert GetQuota(profiles).execute(GetQuotaInput(99)).query_limit == 0
    profiles.increment_query_count(4)
    assert profiles.profiles[4].query_count == 10


class Clock:
    def __init__(self, now):
        self.value = now

    def now(self):
        return self.value


class SessionMemory:
    def __init__(self, items=()):
        self.items = {str(item.session_id): item for item in items}
        self.deleted = []

    def get_by_session_id(self, key):
        return self.items.get(key.value)

    def save(self, item):
        self.items[str(item.session_id)] = item
        return item

    def list_expired_before(self, cutoff):
        return tuple(item for item in self.items.values() if item.last_active < cutoff)

    def delete(self, key):
        self.deleted.append(str(key))
        self.items.pop(str(key), None)


class UserMemory:
    def __init__(self):
        self.items = {}
        self.next_id = 1

    def get_by_email(self, email):
        return next((user for user in self.items.values() if user.email == email), None)

    def save(self, user):
        if user.id is None:
            user = replace(user, id=self.next_id)
            self.next_id += 1
        self.items[user.id] = user
        return user


def test_demo_session_and_user_are_created_once_per_identifier():
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    sessions, users, clock = SessionMemory(), UserMemory(), Clock(now)
    first_session = GetOrCreateDemoSession(sessions, clock).execute(DemoSessionInput("abc"))
    second_session = GetOrCreateDemoSession(sessions, clock).execute(DemoSessionInput("abc"))
    assert first_session == second_session
    assert first_session.expires_at == now + DEMO_SESSION_TTL and first_session.expired is False
    user_use_case = GetOrCreateDemoUser(users)
    first_user = user_use_case.execute(DemoSessionInput("abc"))
    assert first_user == user_use_case.execute(DemoSessionInput("abc"))
    assert first_user.email == "demo_abc@demo.local"
    assert users.get_by_email(EmailAddress(first_user.email)).id == first_user.user_id


def test_demo_listing_cleanup_and_missing_repository_identity_contracts():
    users = UserMemory()
    get_user = GetOrCreateDemoUser(users)

    class Lifecycle:
        def __init__(self):
            self.deleted = []

        def list_for_user(self, user_id):
            return (DemoDatasetDTO(dataset_id=1, name="sample", status="ready"),)

        def list_ids_for_user(self, user_id):
            return (1, 2)

        def delete(self, dataset_id, user_id):
            self.deleted.append((dataset_id, user_id))
            if dataset_id == 1:
                raise OSError("dataset cleanup failed")

    lifecycle = Lifecycle()
    request = DemoSessionInput("demo-list")
    assert ListDemoSessionDatasets(get_user, lifecycle).execute(request)[0].dataset_id == 1
    outcome = CleanupDemoSession(get_user, lifecycle).execute(request)
    assert outcome.deleted_dataset_count == 2
    assert lifecycle.deleted == [(1, 1), (2, 1)]

    class MissingIdentity:
        def get_by_email(self, email):
            return None

        def save(self, user):
            return user

    with pytest.raises(RuntimeError, match="identidad"):
        GetOrCreateDemoUser(MissingIdentity()).execute(DemoSessionInput("missing-id"))


def test_user_access_authentication_and_query_usage_delegate_to_fake_ports():
    class DatasetRepo:
        def get_by_id(self, dataset_id):
            return Dataset(user_id=7, name="d", file_path="d.csv", id=dataset_id)

    assert CanAccessDataset(DatasetRepo()).execute(CanAccessDatasetInput(7, 1)).allowed
    assert not CanAccessDataset(DatasetRepo()).execute(CanAccessDatasetInput(8, 1)).allowed

    class Authenticator:
        def authenticate(self, credential):
            return (7, "person@example.com") if credential == "valid" else None

    auth = AuthenticateExternalIdentity(Authenticator())
    assert auth.execute(AuthenticateInput("valid")).email == "person@example.com"
    assert auth.execute(AuthenticateInput("invalid")) is None

    profiles = ProfileMemory()
    IncrementQueryUsage(profiles).execute(7)
    assert profiles.profiles[7].query_count == 1


def test_cleanup_expired_removes_each_session_and_continues_after_dataset_failure():
    now = datetime(2026, 2, 2, tzinfo=timezone.utc)
    sessions = SessionMemory([
        DemoSession(SessionIdentifier("expired"), now - timedelta(days=3), now - timedelta(days=2)),
        DemoSession(SessionIdentifier("active"), now, now),
    ])
    users = UserMemory()
    expired_owner = GetOrCreateDemoUser(users)

    class Lifecycle:
        def list_ids_for_user(self, _user_id):
            return (10, 11)

        def list_for_user(self, _user_id):
            return ()

        def delete(self, dataset_id, user_id):
            if dataset_id == 10:
                raise OSError("external resource unavailable")

    cleanup = CleanupDemoSession(expired_owner, Lifecycle())
    result = CleanupExpiredDemoSessions(sessions, cleanup, Clock(now)).execute()
    assert (result.deleted_session_count, result.deleted_dataset_count) == (1, 2)
    assert sessions.deleted == ["expired"]
    assert "active" in sessions.items


def test_project_status_use_cases_map_entities_and_compose_both_lists():
    class PhaseRepo:
        def list_all(self):
            return (ProjectPhase(id=1, order=1, name="Build", status=ProjectPhaseStatus.COMPLETED),)

    class ModuleRepo:
        def list_all(self):
            return (ProjectModule(id=2, order=1, name="Chat", status=ProjectModuleStatus.LIVE, icon="chat"),)

    phases, modules = ListProjectPhases(PhaseRepo()), ListProjectModules(ModuleRepo())
    status = GetProjectStatus(phases, modules).execute()
    assert status.phases[0].status == "completed"
    assert (status.modules[0].status, status.modules[0].icon) == ("live", "chat")

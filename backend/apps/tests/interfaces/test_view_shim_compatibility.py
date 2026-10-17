def test_legacy_view_shims_reexport_interface_symbols_by_identity():
    from apps.core.interfaces.views import CleanupSessionView as interface_cleanup_view
    from apps.core.views import CleanupSessionView as shim_cleanup_view
    from apps.project_status.interfaces.views import (
        AUTHOR as interface_author,
        ProjectStatusView as interface_project_status_view,
    )
    from apps.project_status.views import (
        AUTHOR as shim_author,
        ProjectStatusView as shim_project_status_view,
    )

    assert shim_cleanup_view is interface_cleanup_view
    assert shim_author is interface_author
    assert shim_project_status_view is interface_project_status_view

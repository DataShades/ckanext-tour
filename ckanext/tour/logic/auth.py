import ckan.plugins.toolkit as tk


def tour_manage(context, data_dict):
    # Sysadmins bypass this check automatically. Override this auth function to
    # grant tour management (list/create/edit/delete/settings) to other users.
    return {"success": False}


@tk.auth_allow_anonymous_access
def tour_list(context, data_dict):
    # public: the tour runtime needs it for anonymous visitors. The action
    # limits non-managers to active tours and strips manager-only fields.
    return {"success": True}


@tk.auth_allow_anonymous_access
def tour_show(context, data_dict):
    # public for the same reason; the action 404s an inactive tour for
    # non-managers and strips manager-only fields.
    return {"success": True}

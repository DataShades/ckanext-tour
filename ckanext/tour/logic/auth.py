def tour_manage(context, data_dict):
    # Sysadmins bypass this check automatically. Override this auth function to
    # grant tour management (list/create/edit/delete/settings) to other users.
    return {"success": False}


def tour_list(context, data_dict):
    return {"success": True}


def tour_show(context, data_dict):
    return {"success": True}

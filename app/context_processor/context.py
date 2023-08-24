from ..models import InviteEmploye

def user_role(request):
    if request.user.is_authenticated:
        user_manager = request.user.manager

        if user_manager != None:
            invite = InviteEmploye.objects.get(invited_by=user_manager, selected_user=request.user)
            user_role = invite.role
            user_permission = invite.permission
        else:
            user_role = 'ADMIN'
            user_permission = 'WRITE'
    else:
        user_role = 'ADMIN'
        user_permission = 'WRITE'

    return {'user_role': user_role, 'permission': user_permission}


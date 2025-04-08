def user_group(request):
    us_bel = request.user.groups.filter(name='users_div_no_warehouses_edit').exists() or request.user.is_superuser
    return {
        'us_bel': us_bel
    }
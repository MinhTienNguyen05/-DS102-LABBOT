MENU_ITEMS = [
    {'name': 'Home', 'url': '/', 'icon_path': 'components/icon/home.html'},
    {'name': 'Products', 'url': '/products/', 'icon_path': 'components/icon/laptop.html'},
    {'name': 'Chat', 'url': '/chat/', 'icon_path': 'components/icon/chat.html'},
]

def global_variables(request):
    return {
        'current_path': request.path,
        'menu_items': MENU_ITEMS
    }
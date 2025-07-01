from django.shortcuts import redirect, render
from userauths.forms import UserRegisterForm
from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.views.decorators.csrf import csrf_protect
import logging

logger = logging.getLogger(__name__)


# Create your views here.
@csrf_protect
def register_view(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST or None)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Hey {username}, your account was created successfully!!')

            new_user = authenticate(
                username=form.cleaned_data.get('email'),
                password=form.cleaned_data.get('password1')
            )

            login(request, new_user)

            return redirect('chat:index') # ('app_name:url_name')

    else:
        form = UserRegisterForm()
        print('HELOOOO???')

    logger.debug("Debug message")
    logger.info("Some info")
    logger.error("Something went wrong")


    context = {
        'form': form
    }

    return render(request, 'userauths/sign-up.html', context)
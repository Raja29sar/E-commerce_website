from django.shortcuts import render,redirect
from .forms import RegistrationForm
from .models import Account
from django.contrib import messages,auth
from orders.models import Order
from django.contrib.auth import authenticate,login as auth_login
from django.http import HttpResponseRedirect

from django.contrib.auth.decorators import login_required
from carts.views import _cart_id
from carts.models import Cart, CartItem
import requests

def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            phone_number = form.cleaned_data['phone_number']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            username = email.split("@")[0]
            user = Account.objects.create_user(first_name=first_name, last_name=last_name, email=email, username=username, password=password)
            user.phone_number = phone_number
            user.save()
            messages.success(request, 'Registration successful')
            return redirect('register')
    else:
        form = RegistrationForm()        
    form = RegistrationForm()        

    form = RegistrationForm()
    context ={
        'form' : form,
    }
    return render(request,'accounts/register.html',context)

def login(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']

        user = auth.authenticate(email=email, password=password)

        if user is not None:
            try:
                cart = Cart.objects.get(cart_id=_cart_id(request))
                is_cart_item_exists = CartItem.objects.filter(cart=cart).exists()
                if is_cart_item_exists:
                    cart_item = CartItem.objects.filter(cart=cart)

                    product_variation = []
                    for item in cart_item:
                        variation = item.variations.all()
                        product_variation.append(list(variation))

                    cart_item = CartItem.objects.filter(user=user)
                    ex_var_list = []
                    id = []
                    for item in cart_item:
                        existing_variation = item.variations.all()
                        ex_var_list.append(list(existing_variation))
                        id.append(item.id)    


                    for pr in product_variation:
                        if pr in ex_var_list:
                            index = ex_var_list.index(pr)
                            item_id = id[index]
                            item = CartItem.objects.get(id=item_id)
                            item.quantity += 1
                            item.user = user
                            item.save()  

                    else:
                        cart_item = CartItem.objects.filter(cart=cart)          
                        for item in cart_item:
                            item.user = user
                            item.save()
            except:
                pass

            auth.login(request, user)
            messages.success(request, 'You are now logged in.')


            url = request.META.get('HTTP_REFERER')
            try:
                query = requests.utils.urlparse(url).query

                params = dict(x.split('=') for x in query.split('&'))
                if 'next' in params:
                    nextPage = params['next']
                    return redirect(nextPage)
            except:
                return redirect('dashboard')

            # url = request.META.get('HTTP_REFERER')
            # if url:
            #     try:
            #         query = requests.utils.urlparse(url).query
            #         print(f"Query string: {query}")
            #         params = dict(x.split('=') for x in query.split('&'))
            #         print(f"Params: {params}")
            #         if 'next' in params:
            #             nextPage = params['next']
            #             return redirect(nextPage)
                    
            #     except Exception as e:
            #         print(f"Error parsing URL: {e}")    
            #         pass

            # return redirect('dashboard')    



        else:
            messages.error(request, 'Invalid login credentials')
            return redirect('login')
    return render(request,'accounts/login.html')

# def login(request):
#     context = {}
#     if request.method == 'POST':
#         email = request.POST['email']
#         password = request.POST['password']

#         user = authenticate(email=email, password=password)
#         if user is not None:
#             auth_login(request, user)
#             if user.is_staff:
#                 return HttpResponseRedirect('/store')
#             else:
#                 return HttpResponseRedirect('/store')
#         else:
#             messages.add_message(request, messages.INFO, 'Invalid Login Details!')

#     return render(request, 'accounts/login.html', context)  

@login_required(login_url= 'login')
def logout(request):
    auth.logout(request)
    messages.success(request, 'You are logged out.')
    return redirect('login')

@login_required(login_url= 'login')
def dashboard(request):
    orders = Order.objects.order_by('-created_at').filter(user_id=request.user.id, is_ordered=True)
    orders_count = orders.count()
    context = {
        'orders_count' : orders_count,
    }
    return render(request, 'accounts/dashboard.html',context)

def my_orders(request):
    orders = Order.objects.filter(user=request.user, is_ordered=True).order_by('-created_at')
    context = {
        'orders': orders,
    }
    return render(request, 'accounts/my_orders.html',context)
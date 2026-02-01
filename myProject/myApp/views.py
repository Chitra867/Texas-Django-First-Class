from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from .forms import SignupForm
from django.contrib.auth.models import User
from django.contrib import messages
from .models import Product, Category, Cart
from django.contrib.auth import authenticate, login
from .forms import CustomerProfileForm

def home(request):
    products = Product.objects.all()[:8]
    featured_products = Product.objects.filter(featured=True)[:4]
    categories = Category.objects.all()

    return render(request, 'home.html', {
        'products': products,
        'featured_products': featured_products,
        'categories': categories
    })

def about(request):
    return render(request, 'about.html')

def contact(request):
    return render(request, 'contact.html')

def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            next_url = request.GET.get('next', 'home')
            return redirect(next_url)
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def profile_view(request):
    customer = request.user.customer

    if request.method == "POST":
        form = CustomerProfileForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully!")
            return redirect('home') 
    else:
        form = CustomerProfileForm(instance=customer)

    return render(request, "myApp/profile.html", {"form": form})


@login_required
def cart_view(request):
    cart_items = Cart.objects.filter(user=request.user)
    total = sum(item.total_price() for item in cart_items)
    return render(request, 'cart.html', {
        'cart_items': cart_items,
        'total': total
    })

@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if product.stock <= 0:
        return redirect('cart')

    cart_item, created = Cart.objects.get_or_create(
        user=request.user,
        product=product
    )

    if not created:
        cart_item.quantity += 1
    else:
        cart_item.quantity = 1

    cart_item.save()

    product.stock -= 1
    product.save()

    return redirect('cart')

@login_required
def remove_from_cart(request, cart_id):
    Cart.objects.filter(id=cart_id, user=request.user).delete()
    return redirect('cart')


def products(request):
    products_qs = Product.objects.select_related('category').all()
    categories = Category.objects.all()

    search_query = request.GET.get('search', '')
    selected_category = request.GET.get('category', '')

    if search_query:
        products_qs = products_qs.filter(name__icontains=search_query)

    if selected_category:
        products_qs = products_qs.filter(category_id=selected_category)

    paginator = Paginator(products_qs, 6)  # products per page
    page_number = request.GET.get('page')
    products_page = paginator.get_page(page_number)

    context = {
        'products': products_page,
        'categories': categories,
        'search_query': search_query,
        'selected_category': int(selected_category) if selected_category else '',
    }

    return render(request, 'products.html', context)

def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    return render(request, 'product_detail.html', {'product': product})




def login_signup_view(request):

    if request.method == "POST":
        action = request.POST.get("action")

        # 🔐 LOGIN
        if action == "login":
            username = request.POST.get("username")
            password = request.POST.get("password")

            user = authenticate(request, username=username, password=password)

            if user:
                login(request, user)
                return redirect("profile")  # change if needed
            else:
                messages.error(request, "Invalid username or password")

        # 📝 SIGNUP
        elif action == "signup":
            form = SignupForm(request.POST)
            if form.is_valid():
                user = form.save(commit=False)
                user.set_password(form.cleaned_data["password"])
                user.save()  # 🔥 SIGNAL CREATES CUSTOMER
                messages.success(request, "Account created successfully")
                return redirect("login")

    return render(request, "myApp/login.html")
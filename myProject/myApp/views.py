from django.db import transaction

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.contrib import messages
from django.http import JsonResponse


from .models import Product, Category, Cart, Wishlist, Customer, Order, OrderItem
from .forms import SignupForm, CustomerProfileForm

def home(request):
    query = request.GET.get('q', '')

    if query:
        products = Product.objects.filter(name__icontains=query)
    else:
        products = Product.objects.all()[:8]
    featured_products = Product.objects.filter(featured=True)[:4]
    categories = Category.objects.all()

    wishlist_ids = []
    if request.user.is_authenticated:
        wishlist_ids = Wishlist.objects.filter(
            user=request.user
        ).values_list("product_id", flat=True)

    return render(request, 'home.html', {
        'products': products,
        'featured_products': featured_products,
        'categories': categories,
        'wishlist_ids': wishlist_ids,
        'query': query,
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
            user = form.get_user()
            login(request, user)

            customer, _ = Customer.objects.get_or_create(user=user)

            if not customer.profile_completed:
                return redirect('profile')
            return redirect('home')
    else:
        form = AuthenticationForm()

    return render(request, 'login.html', {'form': form})



def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def profile_view(request):
    customer, created = Customer.objects.get_or_create(user=request.user)

    # 🚫 Do not show form again
    if customer.profile_completed:
        return redirect('home')

    if request.method == "POST":
        form = CustomerProfileForm(request.POST, instance=customer)
        if form.is_valid():
            customer = form.save(commit=False)
            customer.profile_completed = True
            customer.save()
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
        messages.error(request, "Product is out of stock")
        return redirect("home")

    cart_item, created = Cart.objects.get_or_create(
        user=request.user,
        product=product
    )

    if not created:
        cart_item.quantity += 1
    else:
        cart_item.quantity = 1

    cart_item.save()
    return redirect("cart")



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
    product.views += 1
    product.save(update_fields=['views'])


    return render(request, 'product_detail.html', {'product': product})


@login_required
def toggle_wishlist(request):
    if request.method == "POST":
        product_id = request.POST.get("product_id")
        product = get_object_or_404(Product, id=product_id)

        wishlist, created = Wishlist.objects.get_or_create(
            user=request.user,
            product=product
        )

        if not created:
            wishlist.delete()
            return JsonResponse({"status": "removed"})
        else:
            return JsonResponse({"status": "added"})

    return JsonResponse({"error": "Invalid request"}, status=400)


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
                customer, _ = Customer.objects.get_or_create(user=user)

                if not customer.profile_completed:
                    return redirect("profile")
                return redirect("home")
            else:
                messages.error(request, "Invalid username or password")

        # 📝 SIGNUP
        elif action == "signup":
            form = SignupForm(request.POST)
            if form.is_valid():
                user = form.save(commit=False)
                user.set_password(form.cleaned_data["password"])
                user.save()
                messages.success(request, "Account created successfully")
                return redirect("login")

    return render(request, "myApp/login.html")


@login_required
@transaction.atomic
def checkout_view(request):
    cart_items = Cart.objects.filter(user=request.user)

    if not cart_items.exists():
        return redirect('cart')

    total = sum(item.product.price * item.quantity for item in cart_items)

    if request.method == "POST":
        # Validate stock BEFORE order
        for item in cart_items:
            if item.product.stock < item.quantity:
                messages.error(
                    request,
                    f"{item.product.name} is out of stock."
                )
                return redirect("checkout")

        order = Order.objects.create(
            user=request.user,
            total_price=total,
            is_ordered=True
        )

        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price=item.product.price
            )

            item.product.stock -= item.quantity
            item.product.save()

        cart_items.delete()
        return redirect("order_success", order_id=order.id)

    return render(request, "checkout.html", {
        "cart_items": cart_items,
        "total": total
    })

@login_required
def order_success_view(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    order_items = order.items.all()   # related_name="items"
    customer = Customer.objects.get(user=request.user)

    return render(request, "order_success.html", {
        "order": order,
        "order_items": order_items,
    })


@login_required
def my_orders_view(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'my_orders.html', {'orders': orders})
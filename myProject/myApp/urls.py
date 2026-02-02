from django.urls import path
from . import views


urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),

    # Authentication
    path('register/', views.register_view, name='register'),
    path('login/', views.login_signup_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),

    # Cart
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('remove-from-cart/<int:cart_id>/', views.remove_from_cart, name='remove_from_cart'),
    

     # ✅ Wishlist (AJAX ONLY)
    path('wishlist/toggle/', views.toggle_wishlist, name='toggle_wishlist'),



    path('profile/', views.profile_view, name='profile'),

path('checkout/', views.checkout_view, name='checkout'),
    path("order-success/<int:order_id>/", views.order_success_view, name="order_success"),

path('my-orders/', views.my_orders_view, name='my_orders'),
]

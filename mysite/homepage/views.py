from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.db.models import Q, Avg
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from .models import Product, Cart, CartItem, Category, Review, Wishlist, Order
import uuid


def get_cart(request):
	if request.user.is_authenticated:
		cart, _ = Cart.objects.get_or_create(user=request.user)
		return cart
	session_key = request.session.get('cart_session_key')
	if not session_key:
		session_key = uuid.uuid4().hex
		request.session['cart_session_key'] = session_key
	cart, _ = Cart.objects.get_or_create(session_key=session_key)
	return cart


def product_list(request):
	products = Product.objects.prefetch_related('category', 'reviews')
	categories = Category.objects.all()
	
	# Search functionality
	search = request.GET.get('search', '').strip()
	if search:
		products = products.filter(
			Q(name__icontains=search) | 
			Q(description__icontains=search)
		)
	
	# Category filter
	category = request.GET.get('category', '').strip()
	if category:
		products = products.filter(category__slug=category)
	
	# Price filter
	min_price = request.GET.get('min_price', '')
	max_price = request.GET.get('max_price', '')
	if min_price:
		try:
			products = products.filter(price__gte=float(min_price))
		except:
			pass
	if max_price:
		try:
			products = products.filter(price__lte=float(max_price))
		except:
			pass
	
	# Rating filter
	rating = request.GET.get('rating', '')
	if rating:
		try:
			products = products.filter(rating__gte=float(rating))
		except:
			pass
	
	# Sorting
	sort = request.GET.get('sort', '-created')
	if sort in ['price', '-price', 'name', 'rating', '-rating', '-created']:
		products = products.order_by(sort)
	
	# Stock status filter
	in_stock = request.GET.get('in_stock')
	if in_stock == 'yes':
		products = products.filter(stock__gt=0)
	
	# Featured/New filters
	featured = request.GET.get('featured')
	if featured == 'yes':
		products = products.filter(is_featured=True)
	
	context = {
		'products': products,
		'categories': categories,
		'search': search,
		'selected_category': category,
		'sort': sort,
	}
	return render(request, 'homepage/product_list.html', context)


def product_detail(request, slug):
	product = get_object_or_404(Product, slug=slug)
	reviews = product.reviews.all().order_by('-created')
	avg_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0
	related_products = Product.objects.filter(
		category=product.category
	).exclude(id=product.id)[:4]
	
	context = {
		'product': product,
		'reviews': reviews,
		'avg_rating': avg_rating,
		'review_count': reviews.count(),
		'related_products': related_products,
	}
	return render(request, 'homepage/product_detail.html', context)


def cart_view(request):
	cart = get_cart(request)
	return render(request, 'homepage/cart.html', {'cart': cart})


def add_to_cart(request):
	if request.method != 'POST':
		return redirect('product_list')
	product_id = request.POST.get('product_id')
	qty = int(request.POST.get('quantity', 1))
	product = get_object_or_404(Product, id=product_id)
	
	if product.stock < qty:
		messages.error(request, f'Only {product.stock} items available.')
		return redirect('product_detail', slug=product.slug)
	
	cart = get_cart(request)
	item, created = CartItem.objects.get_or_create(cart=cart, product=product)
	if not created:
		if item.quantity + qty > product.stock:
			messages.error(request, f'Cannot add more. Only {product.stock} available.')
			return redirect('cart_view')
		item.quantity += qty
	else:
		item.quantity = qty
	item.save()
	messages.success(request, f'✓ Added {product.name} to cart.')
	return redirect('cart_view')


def remove_from_cart(request, item_id):
	cart = get_cart(request)
	item = get_object_or_404(CartItem, id=item_id, cart=cart)
	product_name = item.product.name
	item.delete()
	messages.info(request, f'✓ Removed {product_name} from cart.')
	return redirect('cart_view')


@require_http_methods(["POST"])
def update_cart_item(request, item_id):
	cart = get_cart(request)
	item = get_object_or_404(CartItem, id=item_id, cart=cart)
	quantity = int(request.POST.get('quantity', 1))
	
	if quantity < 1:
		item.delete()
		return redirect('cart_view')
	
	if quantity > item.product.stock:
		messages.error(request, f'Only {item.product.stock} available.')
		return redirect('cart_view')
	
	item.quantity = quantity
	item.save()
	messages.success(request, 'Cart updated.')
	return redirect('cart_view')


def checkout(request):
	cart = get_cart(request)
	if request.method == 'POST':
		name = request.POST.get('customer_name', '').strip()
		email = request.POST.get('email', '').strip()
		phone = request.POST.get('contact_number', '').strip()
		address = request.POST.get('address', '').strip()
		city = request.POST.get('city', '').strip()
		postal = request.POST.get('postal_code', '').strip()
		payment = request.POST.get('payment_method', 'cod')
		notes = request.POST.get('notes', '').strip()
		
		if not name or not phone or not address:
			messages.error(request, 'Please fill in all required fields.')
			return redirect('checkout')
		
		if not cart.items.exists():
			messages.error(request, 'Your cart is empty.')
			return redirect('cart_view')
		
		from .models import Order, OrderItem
		
		order = Order.objects.create(
			user=request.user if request.user.is_authenticated else None,
			customer_name=name,
			email=email,
			phone=phone,
			address=address,
			city=city,
			postal_code=postal,
			status='confirmed',
			payment_method=payment,
			notes=notes,
		)
		
		for item in cart.items.select_related('product').all():
			OrderItem.objects.create(
				order=order,
				product=item.product,
				quantity=item.quantity,
				price=item.product.final_price,
			)
			# Update stock
			item.product.stock -= item.quantity
			item.product.save()
		
		cart.items.all().delete()
		messages.success(request, f'✓ Order placed successfully! Order ID: {order.order_number}')
		return redirect('order_confirmation', order_id=order.id)
	
	return render(request, 'homepage/checkout.html', {'cart': cart})


def order_confirmation(request, order_id):
	order = get_object_or_404(Order, id=order_id)
	return render(request, 'homepage/order_confirmation.html', {'order': order})


def order_history(request):
	if not request.user.is_authenticated:
		messages.error(request, 'Please login to view orders.')
		return redirect('login')
	
	orders = Order.objects.filter(user=request.user).prefetch_related('items')
	return render(request, 'homepage/order_history.html', {'orders': orders})


def add_review(request, product_id):
	if not request.user.is_authenticated:
		messages.error(request, 'Please login to add a review.')
		return redirect('login')  # Uses Django's built-in auth URL
	
	product = get_object_or_404(Product, id=product_id)
	
	if request.method == 'POST':
		rating = int(request.POST.get('rating', 3))
		title = request.POST.get('title', '').strip()
		comment = request.POST.get('comment', '').strip()
		
		if not comment:
			messages.error(request, 'Please add a comment.')
		else:
			review, created = Review.objects.update_or_create(
				product=product,
				user=request.user,
				defaults={
					'rating': rating,
					'title': title,
					'comment': comment,
				}
			)
			messages.success(request, '✓ Review submitted successfully!')
	
	return redirect('product_detail', slug=product.slug)


def wishlist_view(request):
	if not request.user.is_authenticated:
		messages.error(request, 'Please login to view wishlist.')
		return redirect('login')
	
	wishlist, _ = Wishlist.objects.get_or_create(user=request.user)
	return render(request, 'homepage/wishlist.html', {'wishlist': wishlist})


def add_to_wishlist(request, product_id):
	if not request.user.is_authenticated:
		messages.error(request, 'Please login to add to wishlist.')
		return redirect('login')
	
	product = get_object_or_404(Product, id=product_id)
	wishlist, _ = Wishlist.objects.get_or_create(user=request.user)
	
	if product in wishlist.products.all():
		wishlist.products.remove(product)
		messages.success(request, 'Removed from wishlist.')
	else:
		wishlist.products.add(product)
		messages.success(request, 'Added to wishlist.')
	
	return redirect('product_detail', slug=product.slug)


def remove_from_wishlist(request, product_id):
	if not request.user.is_authenticated:
		return redirect('login')
	
	product = get_object_or_404(Product, id=product_id)
	wishlist = get_object_or_404(Wishlist, user=request.user)
	wishlist.products.remove(product)
	messages.success(request, 'Removed from wishlist.')
	return redirect('wishlist_view')


def search_products(request):
	query = request.GET.get('q', '').strip()
	if len(query) < 2:
		return render(request, 'homepage/search.html', {'query': query, 'products': []})
	
	products = Product.objects.filter(
		Q(name__icontains=query) |
		Q(description__icontains=query) |
		Q(category__name__icontains=query)
	).distinct()
	
	return render(request, 'homepage/search.html', {
		'query': query,
		'products': products,
		'result_count': products.count(),
	})


def signup(request):
	if request.user.is_authenticated:
		return redirect('product_list')
	
	if request.method == 'POST':
		username = request.POST.get('username', '').strip()
		email = request.POST.get('email', '').strip()
		password = request.POST.get('password', '').strip()
		password_confirm = request.POST.get('password_confirm', '').strip()
		
		if not username or not email or not password:
			messages.error(request, 'Please fill in all fields.')
			return redirect('signup')
		
		if password != password_confirm:
			messages.error(request, 'Passwords do not match.')
			return redirect('signup')
		
		if len(password) < 6:
			messages.error(request, 'Password must be at least 6 characters.')
			return redirect('signup')
		
		if User.objects.filter(username=username).exists():
			messages.error(request, 'Username already taken.')
			return redirect('signup')
		
		if User.objects.filter(email=email).exists():
			messages.error(request, 'Email already registered.')
			return redirect('signup')
		
		user = User.objects.create_user(
			username=username,
			email=email,
			password=password
		)
		
		login(request, user)
		messages.success(request, f'✓ Welcome {username}! Your account has been created.')
		return redirect('product_list')
	
	return render(request, 'homepage/signup.html')

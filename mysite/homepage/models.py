from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator


class Category(models.Model):
	name = models.CharField(max_length=200, unique=True)
	slug = models.SlugField(max_length=200, unique=True)
	description = models.TextField(blank=True)
	icon = models.CharField(max_length=50, blank=True, default='fa-box')

	class Meta:
		ordering = ['name']
		verbose_name_plural = 'Categories'

	def __str__(self):
		return self.name


class Product(models.Model):
	name = models.CharField(max_length=200)
	slug = models.SlugField(max_length=200, unique=True)
	description = models.TextField(blank=True)
	price = models.DecimalField(max_digits=10, decimal_places=2)
	discount_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
	stock = models.PositiveIntegerField(default=0)
	category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
	image = models.ImageField(upload_to='products/', blank=True, null=True)
	rating = models.DecimalField(max_digits=3, decimal_places=2, default=0, validators=[MinValueValidator(0), MaxValueValidator(5)])
	is_featured = models.BooleanField(default=False)
	is_new = models.BooleanField(default=True)
	created = models.DateTimeField(auto_now_add=True)
	updated = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ['-created']
		indexes = [models.Index(fields=['slug']), models.Index(fields=['category'])]

	def __str__(self):
		return self.name

	@property
	def final_price(self):
		return self.discount_price if self.discount_price else self.price

	@property
	def discount_percentage(self):
		if self.discount_price:
			discount = (self.price - self.discount_price) / self.price * 100
			return int(discount)
		return 0


class Review(models.Model):
	product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
	user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
	rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
	title = models.CharField(max_length=200, blank=True)
	comment = models.TextField()
	helpful_count = models.PositiveIntegerField(default=0)
	created = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['-created']
		unique_together = ('product', 'user')

	def __str__(self):
		return f"Review of {self.product.name} by {self.user or 'Anonymous'}"


class Wishlist(models.Model):
	user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wishlist')
	products = models.ManyToManyField(Product, related_name='wishlisted_by')
	created = models.DateTimeField(auto_now_add=True)
	updated = models.DateTimeField(auto_now=True)

	def __str__(self):
		return f"Wishlist of {self.user.username}"


class Cart(models.Model):
	user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.CASCADE)
	session_key = models.CharField(max_length=40, blank=True, db_index=True)
	created = models.DateTimeField(auto_now_add=True)
	updated = models.DateTimeField(auto_now=True)

	def __str__(self):
		return f"Cart {self.id} ({self.user or self.session_key})"

	@property
	def total(self):
		return sum(item.line_total for item in self.items.select_related('product').all())

	@property
	def item_count(self):
		return sum(item.quantity for item in self.items.all())


class CartItem(models.Model):
	cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE)
	product = models.ForeignKey(Product, on_delete=models.CASCADE)
	quantity = models.PositiveIntegerField(default=1)
	added_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

	class Meta:
		unique_together = ('cart', 'product')

	def __str__(self):
		return f"{self.quantity} x {self.product.name}"

	@property
	def line_total(self):
		return self.product.final_price * self.quantity


class Order(models.Model):
	STATUS_CHOICES = (
		('pending', 'Pending'),
		('confirmed', 'Confirmed'),
		('processing', 'Processing'),
		('shipped', 'Shipped'),
		('delivered', 'Delivered'),
		('cancelled', 'Cancelled'),
		('returned', 'Returned'),
	)

	order_number = models.CharField(max_length=20, unique=True, editable=False, default='')
	user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='orders')
	customer_name = models.CharField(max_length=200)
	email = models.EmailField(blank=True)
	phone = models.CharField(max_length=20)
	address = models.TextField()
	city = models.CharField(max_length=100, blank=True)
	postal_code = models.CharField(max_length=20, blank=True)
	status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
	payment_method = models.CharField(max_length=50, default='cod', choices=[('cod', 'Cash on Delivery'), ('card', 'Credit Card')])
	notes = models.TextField(blank=True)
	created = models.DateTimeField(auto_now_add=True)
	updated = models.DateTimeField(auto_now=True)
	shipped_date = models.DateTimeField(null=True, blank=True)

	class Meta:
		ordering = ['-created']

	def __str__(self):
		return f"Order {self.order_number}"

	def save(self, *args, **kwargs):
		if not self.order_number:
			import uuid
			self.order_number = f"ORD-{uuid.uuid4().hex[:8].upper()}"
		super().save(*args, **kwargs)

	@property
	def total(self):
		return sum(item.line_total for item in self.items.select_related('product').all())


class OrderItem(models.Model):
	order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
	product = models.ForeignKey(Product, on_delete=models.PROTECT)
	quantity = models.PositiveIntegerField(default=1)
	price = models.DecimalField(max_digits=10, decimal_places=2)

	def __str__(self):
		return f"{self.quantity} x {self.product.name} (@{self.price})"

	@property
	def line_total(self):
		return self.price * self.quantity

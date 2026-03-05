from django.contrib import admin
from django.utils.html import format_html
from .models import Product, Cart, CartItem, Order, OrderItem, Category, Review, Wishlist


# Category Admin
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
	list_display = ('name', 'slug')
	prepopulated_fields = {'slug': ('name',)}
	search_fields = ('name',)


# Review Admin
@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
	list_display = ('product', 'user', 'rating', 'created')
	list_filter = ('rating', 'created')
	search_fields = ('product__name', 'user__username', 'comment')
	readonly_fields = ('created',)


# Wishlist Admin
@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
	list_display = ('user', 'product_count', 'updated')
	search_fields = ('user__username',)

	def product_count(self, obj):
		return obj.products.count()
	product_count.short_description = 'Products'


# Cart Item Inline
class CartItemInline(admin.TabularInline):
	model = CartItem
	readonly_fields = ('product', 'quantity', 'added_at')
	extra = 0


# Order Item Inline
class OrderItemInline(admin.TabularInline):
	model = OrderItem
	fields = ('product', 'quantity', 'price', 'line_total')
	readonly_fields = ('product', 'quantity', 'price', 'line_total')
	extra = 0

	def line_total(self, obj):
		return f"${obj.line_total}"
	line_total.short_description = 'Total'


# Product Admin
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
	list_display = ('name', 'category', 'price', 'discount_price', 'stock', 'rating', 'is_featured', 'is_new', 'created')
	list_filter = ('category', 'is_featured', 'is_new', 'created', 'rating')
	search_fields = ('name', 'description')
	prepopulated_fields = {'slug': ('name',)}
	fieldsets = (
		('Basic Info', {'fields': ('name', 'slug', 'category', 'description', 'image')}),
		('Pricing', {'fields': ('price', 'discount_price')}),
		('Inventory', {'fields': ('stock',)}),
		('Display', {'fields': ('rating', 'is_featured', 'is_new')}),
		('Timestamps', {'fields': ('created', 'updated'), 'classes': ('collapse',)}),
	)
	readonly_fields = ('created', 'updated')


# Cart Admin
@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
	list_display = ('id', 'user_or_session', 'item_count', 'total', 'created', 'updated')
	list_filter = ('created', 'updated')
	search_fields = ('user__username', 'session_key')
	inlines = [CartItemInline]

	def user_or_session(self, obj):
		return obj.user.username if obj.user else f"Session: {obj.session_key[:8]}"
	user_or_session.short_description = 'User/Session'


# Order Admin
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
	list_display = ('order_number', 'customer_name', 'status', 'total', 'payment_method', 'created')
	list_filter = ('status', 'payment_method', 'created')
	search_fields = ('order_number', 'customer_name', 'email', 'phone')
	readonly_fields = ('order_number', 'total', 'created', 'updated')
	inlines = [OrderItemInline]
	fieldsets = (
		('Order Info', {'fields': ('order_number', 'status', 'payment_method', 'created', 'updated', 'shipped_date')}),
		('Customer Info', {'fields': ('user', 'customer_name', 'email', 'phone')}),
		('Shipping Address', {'fields': ('address', 'city', 'postal_code')}),
		('Notes', {'fields': ('notes',), 'classes': ('collapse',)}),
	)

	def total(self, obj):
		return f"${obj.total}"
	total.short_description = 'Order Total'

	can_delete = False

	def order_link(self, obj):
		order = obj.order
		return format_html("<div>#{}</div><div>{}</div>", order.id, order.customer_name)
	order_link.short_description = 'Checked out by'

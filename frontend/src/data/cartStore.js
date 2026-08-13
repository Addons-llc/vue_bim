import { computed, ref } from 'vue'

const CART_STORAGE_KEY = 'buyInMinutesCart'

function readStoredCart() {
  try {
    return JSON.parse(localStorage.getItem(CART_STORAGE_KEY)) || []
  } catch {
    return []
  }
}

function saveCart(items) {
  localStorage.setItem(CART_STORAGE_KEY, JSON.stringify(items))
}

const cartItems = ref(readStoredCart())

export const cartProducts = cartItems

export const cartItemCount = computed(() => cartItems.value.length)

export const cartTotal = computed(() =>
  cartItems.value.reduce((total, item) => total + item.price * item.quantity, 0),
)

export function addProductToCart(product) {
  const existingItem = cartItems.value.find((item) => item.id === product.id)
  let cartItem

  if (existingItem) {
    existingItem.quantity += 1
    cartItem = existingItem
  } else {
    cartItem = {
      id: product.id,
      itemCode: product.itemCode || product.id,
      name: product.name,
      price: product.price,
      oldPrice: product.oldPrice,
      description: product.description,
      image: product.image,
      supplier: product.supplier || product.supplierDetails?.name || '',
      supplierName: product.supplierName,
      quantity: 1,
    }
    cartItems.value.push(cartItem)
  }

  saveCart(cartItems.value)

  return {
    success: true,
    item: { ...cartItem },
    cart_item_count: cartItemCount.value,
    cart_total: cartTotal.value,
  }
}

export function getCartItems() {
  return cartItems.value
}

export function updateCartProductQuantity(productId, quantity) {
  if (quantity <= 0) {
    removeProductFromCart(productId)
    return
  }

  const existingItem = cartItems.value.find((item) => item.id === productId)

  if (!existingItem) {
    return
  }

  existingItem.quantity = quantity
  saveCart(cartItems.value)
}

export function removeProductFromCart(productId) {
  cartItems.value = cartItems.value.filter((item) => item.id !== productId)
  saveCart(cartItems.value)
}

export function clearCart() {
  cartItems.value = []
  saveCart(cartItems.value)
}

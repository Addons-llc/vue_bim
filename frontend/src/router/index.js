import { createRouter, createWebHashHistory } from 'vue-router'
import BrandsPage from '../pages/BrandsPage.vue'
import BrandDetailsPage from '../pages/BrandDetailsPage.vue'
import CartPage from '../pages/CartPage.vue'
import CategoryDetailsPage from '../pages/CategoryDetailsPage.vue'
import CategoriesPage from '../pages/CategoriesPage.vue'
import HomePage from '../pages/HomePage.vue'
import LoginPage from '../pages/LoginPage.vue'
import OtpPage from '../pages/OtpPage.vue'
import OrdersPage from '../pages/OrdersPage.vue'
import PaymentCancelPage from '../pages/PaymentCancelPage.vue'
import PaymentSuccessPage from '../pages/PaymentSuccessPage.vue'
import ProductDetailsPage from '../pages/ProductDetailsPage.vue'
import ProfilePage from '../pages/ProfilePage.vue'
import StoresPage from '../pages/StoresPage.vue'
import SupplierDetailsPage from '../pages/SupplierDetailsPage.vue'
import WishlistPage from '../pages/WishlistPage.vue'

const routes = [
  {
    path: '/',
    name: 'home',
    component: HomePage,
    props: (route) => ({
      category: route.query.category || '',
      searchText: route.query.search || '',
    }),
  },
  {
    path: '/products',
    redirect: '/',
  },
  {
    path: '/products/:productId',
    name: 'product-details',
    component: ProductDetailsPage,
  },
  {
    path: '/cart',
    name: 'cart',
    component: CartPage,
  },
  {
    path: '/wishlist',
    name: 'wishlist',
    component: WishlistPage,
  },
  {
    path: '/brands',
    name: 'brands',
    component: BrandsPage,
  },
  {
    path: '/brands/:brandName',
    name: 'brand-details',
    component: BrandDetailsPage,
  },
  {
    path: '/stores',
    name: 'stores',
    component: StoresPage,
  },
  {
    path: '/categories',
    name: 'categories',
    component: CategoriesPage,
  },
  {
    path: '/categories/:categoryName',
    name: 'category-details',
    component: CategoryDetailsPage,
  },
  {
    path: '/stores/:categoryName',
    name: 'store-details',
    component: CategoryDetailsPage,
  },
  {
    path: '/suppliers/:supplierName',
    name: 'supplier-details',
    component: SupplierDetailsPage,
  },
  {
    path: '/profile',
    name: 'profile',
    component: ProfilePage,
  },
  {
    path: '/orders',
    name: 'orders',
    component: OrdersPage,
  },
  {
    path: '/payment/success',
    name: 'payment-success',
    component: PaymentSuccessPage,
  },
  {
    path: '/payment/cancel',
    name: 'payment-cancel',
    component: PaymentCancelPage,
  },
  {
    path: '/login',
    name: 'login',
    component: LoginPage,
    meta: {
      layout: 'blank',
    },
  },
  {
    path: '/login/otp',
    name: 'login-otp',
    component: OtpPage,
    meta: {
      layout: 'blank',
    },
  },
  {
    path: '/login/profile',
    name: 'complete-profile',
    component: ProfilePage,
    meta: {
      layout: 'blank',
    },
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/',
  },
]

export const router = createRouter({
  history: createWebHashHistory(),
  routes,
})

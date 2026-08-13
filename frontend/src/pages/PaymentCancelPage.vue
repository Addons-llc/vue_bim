<template>
  <section class="payment-result-page">
    <div class="payment-result-panel">
      <p class="section-label">Payment cancelled</p>
      <h1>Checkout was not completed</h1>
      <p>
        Your cart is still available. You can review it and try payment again.
      </p>
      <RouterLink class="primary-dark-button" :to="{ name: 'cart' }">
        Return to cart
      </RouterLink>
    </div>
  </section>
</template>

<script setup>
const appBase = import.meta.env.BASE_URL
const addSupplierUrl = 'https://addons-bim.m.frappe.cloud/become-a-supplier/new'
const deliveryCompanyUrl = 'https://buyinminutes.u.frappe.cloud/Buy%20In%20Minutes/new.i'
</script>

<template>
  <footer class="app-footer">
    <section class="footer-supplier-section" aria-label="Partner enrollment">
      <a
        class="supplier-dashboard-card"
        :href="addSupplierUrl"
        aria-label="SELL WITH US"
      >
        <div class="supplier-card-copy">
          <h2>SELL WITH US</h2>
          <p>Fast onboarding for trusted market partners.</p>
          <span class="supplier-card-cta">Add now</span>
        </div>
        <img
          class="supplier-card-image"
          src="/supplier-card-image.svg"
          alt=""
          aria-hidden="true"
        />
      </a>

      <a
        class="supplier-dashboard-card delivery-company-card"
        :href="deliveryCompanyUrl"
        aria-label="Enroll a delivery company"
      >
        <div class="supplier-card-copy">
          <h2>Enrollment of delivery companies</h2>
          <p>Fast onboarding for fleet and delivery partners.</p>
          <span class="supplier-card-cta">Enroll now</span>
        </div>
        <img
          class="supplier-card-image"
          src="/delivery-company-card-image.svg"
          alt=""
          aria-hidden="true"
        />
      </a>

      <a
        class="supplier-dashboard-card rider-card"
        :href="deliveryCompanyUrl"
        aria-label="Become a BIM Rider"
      >
        <div class="supplier-card-copy">
          <h2>Become a BIM Rider</h2>
          <p>Join the delivery team and start earning with BIM.</p>
          <span class="supplier-card-cta">Join now</span>
        </div>
        <img
          class="supplier-card-image"
          src="/bim-rider-card-image.svg"
          alt=""
          aria-hidden="true"
        />
      </a>
    </section>

    <div class="footer-inner">
      <section class="footer-brand">
        <a class="footer-logo" :href="appBase" aria-label="Buy In Minutes home">
          <img class="brand-logo" :src="`${appBase}bim.jpeg`" alt="" />
          <span class="brand-name">BIM</span>
        </a>
        <p>
          Fresh vegetables, fruits, grocery, meat, and fish delivered quickly
          from nearby trusted stores.
        </p>

        <div class="app-downloads" aria-label="Download app links">
          <a class="store-badge" href="/app-store">
            <svg
              class="store-icon"
              aria-hidden="true"
              viewBox="0 0 24 24"
              fill="currentColor"
            >
              <path d="M16.2 2.2c.1 1.1-.3 2.1-1 2.9-.8.9-1.9 1.5-3 1.4-.1-1.1.4-2.2 1.1-2.9.8-.8 2-1.4 2.9-1.4Z" />
              <path d="M20.6 17.2c-.4.9-.7 1.4-1.3 2.2-.8 1.2-2 2.7-3.5 2.7-1.3 0-1.7-.8-3.5-.8s-2.3.8-3.5.8c-1.5 0-2.7-1.4-3.5-2.6-2.4-3.6-2.7-7.8-1.2-10.1 1-1.6 2.6-2.5 4.2-2.5 1.6 0 2.6.9 3.9.9 1.2 0 2-.9 3.9-.9 1.4 0 2.9.8 3.9 2.1-3.4 1.9-2.8 6.7.6 8.2Z" />
            </svg>
            <span>
              <small>Download on the</small>
              App Store
            </span>
          </a>

          <a class="store-badge" href="/play-store">
            <span class="store-icon" aria-hidden="true">▶</span>
            <span>
              <small>Get it on</small>
              Google Play
            </span>
          </a>
        </div>
      </section>

      <nav class="footer-links" aria-label="Footer navigation">
        <div>
          <h2>Shop</h2>
          <a href="/products">Vegetables</a>
          <a href="/products">Fruits</a>
          <a href="/products">Grocery</a>
        </div>

        <div>
          <h2>Fresh</h2>
          <a href="/products">Meat</a>
          <a href="/products">Fish</a>
          <a href="/deals">Deals</a>
        </div>

        <div>
          <h2>Support</h2>
          <a href="/orders">Track order</a>
          <a href="/contact">Contact</a>
          <a href="/help">Help</a>
        </div>
      </nav>
    </div>

    <div class="footer-bottom">
      <span>© 2026 BUY IN MINUTES</span>
      <span>Fresh market delivery</span>
    </div>
  </footer>
</template>
